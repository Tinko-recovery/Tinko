from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import User, Transaction, ReconLog
from app.services.payments.razorpay_adapter import RazorpayAdapter

router = APIRouter(tags=["Reconciliation"])


def _parse_int(v: Optional[str], default: int) -> int:
    try:
        return int(v) if v is not None else default
    except Exception:
        return default


@router.post("/run")
def run_recon(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run reconciliation for Razorpay transactions.
    Admin restriction removed (require_roles no longer exists).
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    try:
        adapter = RazorpayAdapter()
    except Exception:
        adapter = None  # When Razorpay creds missing

    txns = db.query(Transaction).filter(
        Transaction.org_id == current_user.org_id,
        Transaction.created_at >= since,
        (Transaction.razorpay_order_id.isnot(None)) |
        (Transaction.razorpay_payment_id.isnot(None))
    ).all()

    checked = 0
    ok = 0
    mismatches = 0

    for txn in txns:
        checked += 1

        internal_status = "paid" if txn.razorpay_payment_id else "unpaid"
        external_status = None

        if adapter and txn.razorpay_order_id:
            try:
                s = adapter.get_order_status(txn.razorpay_order_id)
                external_status = "paid" if s.get("status") == "paid" else "open"
            except Exception:
                external_status = None

        is_ok = (
            (internal_status == "paid" and external_status == "paid") or
            (internal_status == "unpaid" and external_status in ("open", None))
        )

        if is_ok:
            ok += 1
        else:
            mismatches += 1

        log = ReconLog(
            transaction_id=txn.id,
            stripe_checkout_session_id=None,
            stripe_payment_intent_id=None,
            internal_status=internal_status,
            external_status=external_status or "unknown",
            result="ok" if is_ok else "mismatch",
            details={
                "transaction_ref": txn.transaction_ref,
                "razorpay_order_id": txn.razorpay_order_id
            },
        )
        db.add(log)

    db.commit()

    return {
        "checked": checked,
        "ok": ok,
        "mismatches": mismatches
    }
