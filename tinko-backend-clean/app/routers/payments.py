from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..deps import get_db
from .. import models, config
from app.schemas_pkg import payments as schemas
from ..services.pricing_service import calculate_fee
import uuid

router = APIRouter()

@router.post("/create", response_model=schemas.PaymentCreateResponse)
def create_payment(
    payload: schemas.PaymentCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a payment order (Razorpay/Stripe) and record the transaction with fee calculation.
    """
    org = db.query(models.Organization).filter(models.Organization.id == payload.org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # 1. Compute Fee
    fee = calculate_fee(payload.amount, org.service_fee_percent, org.service_fee_fixed)
    net = payload.amount - fee

    # 2. Create Transaction
    txn = models.Transaction(
        transaction_ref=str(uuid.uuid4()),
        amount=payload.amount,
        currency=payload.currency,
        org_id=org.id,
        service_fee=fee,
        net_amount=net
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    # 3. Create Gateway Order
    gateways = org.payment_gateways or []
    
    # Prefer Razorpay if available (or logic to choose)
    if "razorpay" in gateways or (not gateways and config.settings.RAZORPAY_KEY_ID):
        # Razorpay
        try:
            from razorpay import Client as RazorpayClient
            rp = RazorpayClient(auth=(config.settings.RAZORPAY_KEY_ID,
                                     config.settings.RAZORPAY_KEY_SECRET))
            
            razorpay_order = rp.order.create({
                "amount": payload.amount,
                "currency": payload.currency,
                "receipt": txn.transaction_ref,
                "payment_capture": 1 # Auto capture
            })
            
            txn.razorpay_order_id = razorpay_order["id"]
            db.commit()
            
            return {
                "transaction_id": txn.id,
                "gateway": "razorpay",
                "order_id": razorpay_order["id"],
                "key_id": config.settings.RAZORPAY_KEY_ID,
                "amount": payload.amount,
                "currency": payload.currency,
                "description": payload.description or "Payment",
                "service_fee": fee,
                "net_amount": net
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Razorpay Error: {str(e)}")

    elif "stripe" in gateways:
        # Stripe
        try:
            import stripe
            stripe.api_key = config.settings.STRIPE_SECRET_KEY
            
            intent = stripe.PaymentIntent.create(
                amount=payload.amount,
                currency=payload.currency.lower(),
                description=payload.description or "Payment",
                metadata={"transaction_ref": txn.transaction_ref}
            )
            
            txn.stripe_payment_intent_id = intent.id
            db.commit()
            
            return {
                "transaction_id": txn.id,
                "gateway": "stripe",
                "client_secret": intent.client_secret,
                "amount": payload.amount,
                "currency": payload.currency,
                "description": payload.description,
                "service_fee": fee,
                "net_amount": net
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Stripe Error: {str(e)}")

    else:
        raise HTTPException(
            status_code=400,
            detail="No supported payment gateway configured for this organization"
        )
