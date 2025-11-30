from pydantic import BaseModel
from typing import Optional

class PaymentCreateRequest(BaseModel):
    org_id: int
    amount: int               # in paise / cents
    currency: str = "INR"
    description: Optional[str] = None

class PaymentCreateResponse(BaseModel):
    transaction_id: int
    gateway: str
    
    # Razorpay fields
    order_id: Optional[str] = None
    key_id: Optional[str] = None
    
    # Stripe fields
    client_secret: Optional[str] = None
    
    # Common
    amount: int
    currency: str
    description: Optional[str] = None
    
    # Fee Breakdown
    service_fee: int
    net_amount: int
