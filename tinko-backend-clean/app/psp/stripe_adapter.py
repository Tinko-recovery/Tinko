"""Stripe PSP Adapter Implementation."""
import stripe
from typing import Dict, Any, Optional
from .adapter import PSPAdapter, PSPProvider


class StripeAdapter(PSPAdapter):
    """Stripe payment gateway adapter."""
    
    provider = PSPProvider.STRIPE
    
    def __init__(self, api_key: str, api_secret: Optional[str] = None, **kwargs):
        """Initialize Stripe adapter."""
        super().__init__(api_key, api_secret, **kwargs)
        stripe.api_key = self.api_key
        self.webhook_secret = api_secret  # Stripe webhook signing secret
    
    def create_payment_intent(
        self,
        amount: int,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create Stripe payment intent."""
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            metadata=metadata or {},
            **kwargs
        )
        return {
            "intent_id": intent.id,
            "status": self.normalize_status(intent.status),
            "client_secret": intent.client_secret,
            "amount": intent.amount,
            "currency": intent.currency,
            "raw": intent
        }
    
    def retrieve_payment_intent(self, intent_id: str) -> Dict[str, Any]:
        """Retrieve Stripe payment intent."""
        intent = stripe.PaymentIntent.retrieve(intent_id)
        return {
            "intent_id": intent.id,
            "status": self.normalize_status(intent.status),
            "amount": intent.amount,
            "currency": intent.currency,
            "payment_method": intent.payment_method,
            "raw": intent
        }
    
    def create_checkout_session(
        self,
        amount: int,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create Stripe checkout session."""
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': currency,
                    'unit_amount': amount,
                    'product_data': {
                        'name': kwargs.get('product_name', 'Payment Recovery'),
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata or {},
            **{k: v for k, v in kwargs.items() if k != 'product_name'}
        )
        return {
            "session_id": session.id,
            "url": session.url,
            "status": session.status,
            "raw": session
        }

    def create_payment_link(
        self,
        amount: int,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a Stripe Payment Link via Product + Price."""
        # Create product and price
        product = stripe.Product.create(
            name=kwargs.get("product_name", "Payment Recovery"),
            metadata=metadata or {},
        )
        price = stripe.Price.create(
            product=product.id,
            unit_amount=amount,
            currency=currency,
        )
        payment_link = stripe.PaymentLink.create(
            line_items=[{"price": price.id, "quantity": 1}],
            metadata=metadata or {},
        )
        return {
            "payment_link_id": payment_link.id,
            "url": payment_link.url,
            "product_id": product.id,
            "price_id": price.id,
            "raw": payment_link,
        }

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Retrieve a Stripe Checkout Session status and details."""
        sess = stripe.checkout.Session.retrieve(session_id)
        return {
            "session_id": sess.id,
            "status": getattr(sess, "status", None),
            "payment_status": getattr(sess, "payment_status", None),
            "amount_total": getattr(sess, "amount_total", None),
            "currency": getattr(sess, "currency", None),
            "customer_email": getattr(getattr(sess, "customer_details", None), "email", None),
            "payment_intent_id": getattr(sess, "payment_intent", None),
            "raw": sess,
        }
    
    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
        secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verify Stripe webhook signature."""
        webhook_secret = secret or self.webhook_secret
        if not webhook_secret:
            raise ValueError("Webhook secret not configured")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            return {
                "event_id": event.id,
                "type": event.type,
                "data": event.data.object,
                "raw": event
            }
        except stripe.error.SignatureVerificationError as e:
            raise ValueError(f"Invalid webhook signature: {e}")
    
    def refund_payment(
        self,
        payment_id: str,
        amount: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Refund Stripe payment."""
        refund_params = {"payment_intent": payment_id}
        if amount:
            refund_params["amount"] = amount
        if reason:
            refund_params["reason"] = reason
        
        refund = stripe.Refund.create(**refund_params)
        return {
            "refund_id": refund.id,
            "status": refund.status,
            "amount": refund.amount,
            "raw": refund
        }
    
    def normalize_status(self, provider_status: str) -> str:
        """Normalize Stripe status."""
        status_map = {
            "requires_payment_method": "pending",
            "requires_confirmation": "pending",
            "requires_action": "requires_action",
            "processing": "pending",
            "succeeded": "succeeded",
            "canceled": "cancelled",
            "requires_capture": "pending",
        }
        return status_map.get(provider_status, "pending")
