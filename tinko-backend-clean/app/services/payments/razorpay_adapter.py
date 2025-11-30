from __future__ import annotations

import base64
import hashlib
import hmac
import os
from typing import Dict, Any, Optional

import httpx
from .base import PaymentAdapter


class RazorpayAdapter(PaymentAdapter):
    def __init__(self, key_id: Optional[str] = None, key_secret: Optional[str] = None):
        self.key_id = key_id or os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET")
        if not self.key_id or not self.key_secret:
            raise ValueError("Razorpay not configured")
        token = base64.b64encode(f"{self.key_id}:{self.key_secret}".encode()).decode()
        self._auth_header = {"Authorization": f"Basic {token}"}
        self._base = os.getenv("RAZORPAY_API_BASE", "https://api.razorpay.com")

    async def _post(self, path: str, json: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{self._base}{path}", json=json, headers=self._auth_header)
            r.raise_for_status()
            return r.json()

    async def _get(self, path: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{self._base}{path}", headers=self._auth_header)
            r.raise_for_status()
            return r.json()

    def create_order(self, amount: int, currency: str, receipt: str) -> Dict[str, Any]:
        # Synchronous wrapper for convenience in routes/tests using anyio
        import anyio
        return anyio.run(self._create_order_async, amount, currency, receipt)

    async def _create_order_async(self, amount: int, currency: str, receipt: str) -> Dict[str, Any]:
        payload = {"amount": int(amount), "currency": currency.upper(), "receipt": receipt, "payment_capture": 1}
        data = await self._post("/v1/orders", payload)
        return {"order_id": data.get("id"), "amount": data.get("amount"), "currency": data.get("currency")}

    def validate_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
        if not secret:
            raise ValueError("Webhook secret not configured")
        digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(digest, signature):
            raise ValueError("Invalid signature")
        # The payload is JSON; parse and return
        import json
        return json.loads(payload.decode())

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        import anyio
        return anyio.run(self._get_order_status_async, order_id)

    async def _get_order_status_async(self, order_id: str) -> Dict[str, Any]:
        data = await self._get(f"/v1/orders/{order_id}")
        status = data.get("status")  # created, paid, attempted
        return {"status": status, "amount": data.get("amount"), "currency": data.get("currency"), "raw": data}
