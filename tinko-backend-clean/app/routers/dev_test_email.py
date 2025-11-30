from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.email_service import send_failed_payment_alert

router = APIRouter(tags=["Developer Testing"])


class TestFailedPaymentEmail(BaseModel):
    email: str
    customer_name: Optional[str] = "John Doe"
    amount: Optional[str] = "₹1,250"
    order_id: Optional[str] = "ORD-TEST-1234"
    retry_url: str = "https://tinko.in/retry/demo"


@router.post("/test-failed-payment-email")
async def test_failed_payment_email(payload: TestFailedPaymentEmail):
    """
    Developer endpoint to test failed payment recovery email.
    Sends a sample recovery email using SendGrid.
    """

    try:
        send_failed_payment_alert(
            to_email=payload.email,
            customer_name=payload.customer_name,
            amount=payload.amount,
            order_id=payload.order_id,
            retry_url=payload.retry_url,
            merchant_name="Demo Store"
        )
    except Exception as e:
        print("[dev] Test failed payment email error:", e)
        raise HTTPException(status_code=500, detail="Failed to send test email")

    return {"message": "Test failed payment email sent"}
