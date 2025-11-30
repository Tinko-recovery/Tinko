from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Dict, Any


@dataclass
class PaymentIntent:
    id: str
    client_secret: str
    amount: int
    currency: str
    status: str


class PSPAdapter:
    def create_intent(self, *, amount: int, currency: str, description: Optional[str] = None) -> PaymentIntent:
        raise NotImplementedError


class PaymentAdapter(Protocol):
    def create_order(self, amount: int, currency: str, receipt: str) -> Dict[str, Any]:
        """
        Create a PSP order. Returns at least: { order_id, amount, currency }.
        """
        ...

    def validate_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Validate and parse Razorpay webhook. Returns event dict or raises ValueError on invalid signature.
        """
        ...

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Return normalized order status dict { status, amount, currency, raw }.
        """
        ...
