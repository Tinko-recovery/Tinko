from __future__ import annotations

import json
import os
from typing import Any, Dict
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

try:
    import stripe  # type: ignore
except Exception:  # pragma: no cover
    stripe = None  # type: ignore

from ..deps import get_db
from .. import models


router = APIRouter(tags=["webhooks"])


def _extract_txn_ref_from_description(desc: str | None) -> str | None:
    if not desc:
        return None
    prefix = "Recovery for "
    if desc.startswith(prefix):
        return desc[len(prefix) :].strip()
    return None


@router.post("/stripe")
async def webhook_stripe(request: Request, db: Session = Depends(get_db), stripe_signature: str | None = Header(default=None, alias="Stripe-Signature")):
    if stripe is None or not os.getenv("STRIPE_WEBHOOK_SECRET"):
        raise HTTPException(status_code=503, detail="Stripe webhook not configured")

    payload = await request.body()
    # Convert body to dict for logging
    import json
    try:
        payload_dict = json.loads(payload)
    except:
        payload_dict = {"raw": str(payload)}
        
    headers_dict = dict(request.headers)
    
    # 1. Log Raw Webhook
    from app.services.webhook_service import log_webhook, update_webhook_status
    wh_event = log_webhook("stripe", headers_dict, payload_dict, db)

    sig_header = stripe_signature
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)  # type: ignore[attr-defined]
    except Exception as e:  # pragma: no cover
        if wh_event: update_webhook_status(wh_event.id, "failed", f"Invalid signature: {e}", db)
        raise HTTPException(status_code=400, detail=f"Invalid signature: {e}")

    try:
        etype = event.get("type")
        data = event.get("data", {})
        obj: Dict[str, Any] = data.get("object", {})
        pi_id = obj.get("id")
        desc = obj.get("description")
        txn_ref = _extract_txn_ref_from_description(desc)

        # Store an event row for observability
        if txn_ref:
            txn = db.query(models.Transaction).filter(models.Transaction.transaction_ref == txn_ref).first()
        else:
            txn = None

        if not txn:
            # If we can't find the transaction, we can't do recovery.
            # Just log it and return.
            if wh_event: update_webhook_status(wh_event.id, "processed", "Transaction not found", db)
            return {"ok": True, "message": "Transaction not found"}

        if etype == "payment_intent.succeeded":
            # 1. Mark Recovery Attempt as Completed
            attempt = (
                db.query(models.RecoveryAttempt)
                .filter(
                    (models.RecoveryAttempt.transaction_id == txn.id)
                    | (models.RecoveryAttempt.transaction_ref == txn.transaction_ref)
                )
                .order_by(models.RecoveryAttempt.id.desc())
                .first()
            )
            if attempt and attempt.status != "completed":
                attempt.status = "completed"
                attempt.used_at = datetime.utcnow()
                db.commit()
            
            if wh_event: update_webhook_status(wh_event.id, "processed", "Payment Succeeded", db)

        elif etype == "payment_intent.payment_failed":
            # 2. Handle Failure & Smart Retry
            last_error = obj.get("last_payment_error", {})
            error_code = last_error.get("code")
            decline_code = last_error.get("decline_code")
            error_message = last_error.get("message")
            
            # Record Failure Event
            fe = models.FailureEvent(
                transaction_id=txn.id,
                gateway="stripe",
                reason=decline_code or error_code or "payment_failed",
                meta={
                    "payment_intent_id": pi_id,
                    "error_message": error_message,
                    "decline_code": decline_code
                },
            )
            db.add(fe)
            db.commit()

            # Smart Recovery Logic
            from app.services.classifier import classify_event
            from app.services.smart_retry import calculate_smart_delays
            
            # Use decline_code if available as it's more specific for Stripe
            classification = classify_event(decline_code or error_code, error_message)
            delays = calculate_smart_delays(
                classification.get("schedule_strategy"),
                classification.get("delays_minutes")
            )

            # Check if open attempt exists
            existing_attempt = (
                db.query(models.RecoveryAttempt)
                .filter(
                    models.RecoveryAttempt.transaction_id == txn.id,
                    models.RecoveryAttempt.status.in_(["created", "sent", "scheduled"])
                )
                .first()
            )

            if not existing_attempt:
                # Create new recovery attempt
                from secrets import token_urlsafe
                from datetime import timedelta
                
                token = token_urlsafe(16)
                max_delay = max(delays) if delays else 0
                expiry_hours = 24 + (max_delay // 60)
                expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
                
                # Determine channel
                channel = "email"
                if txn.organization and txn.organization.recovery_channels:
                    channel = txn.organization.recovery_channels[0]

                new_attempt = models.RecoveryAttempt(
                    transaction_id=txn.id,
                    transaction_ref=txn.transaction_ref,
                    channel=channel,
                    token=token,
                    status="created",
                    expires_at=expires_at
                )
                db.add(new_attempt)
                db.commit()
                db.refresh(new_attempt)

                # Schedule Retries
                try:
                    from app.tasks.retry_tasks import schedule_retry
                    for delay in delays:
                        schedule_retry(new_attempt.id, txn.org_id, delay_minutes=delay)
                except Exception as e:
                    print(f"Failed to trigger retry: {e}")
            
            if wh_event: update_webhook_status(wh_event.id, "processed", f"Failure recorded. Strategy: {classification.get('schedule_strategy')}", db)

        else:
            if wh_event: update_webhook_status(wh_event.id, "processed", f"Ignored event type: {etype}", db)

        return {"ok": True}

    except Exception as e:
        import traceback
        if wh_event: update_webhook_status(wh_event.id, "failed", str(e) + "\n" + traceback.format_exc(), db)
        return {"ok": False, "error": str(e)}
