from __future__ import annotations

import os
from typing import Optional

try:
    import stripe  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    stripe = None  # type: ignore

from .base import PSPAdapter, PaymentIntent


class StripeAdapter(PSPAdapter):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("STRIPE_SECRET_KEY")
        if stripe is not None:
            stripe.api_key = self.api_key

    def create_intent(self, *, amount: int, currency: str, description: Optional[str] = None) -> PaymentIntent:
        if stripe is None:
            raise RuntimeError("Stripe SDK not available. Install 'stripe' or set up mocks.")
        pi = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            description=description,
            automatic_payment_methods={"enabled": True},
        )
        return PaymentIntent(
            id=pi["id"],
            client_secret=pi["client_secret"],
            amount=pi["amount"],
            currency=pi["currency"],
            status=pi["status"],
        )
