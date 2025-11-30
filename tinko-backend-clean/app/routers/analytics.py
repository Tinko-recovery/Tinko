"""
Analytics API endpoints (Razorpay-agnostic; org-scoped).
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import Optional

from app.db import get_db
from app.deps import get_current_user
from app.models import User, Transaction, RecoveryAttempt, FailureEvent

router = APIRouter(tags=["Analytics"])


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


@router.get("/revenue_recovered")
def revenue_recovered(
    from_: Optional[str] = Query(None, alias="from"),
    to_: Optional[str] = Query(None, alias="to"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start = _parse_dt(from_) or datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = _parse_dt(to_) or datetime.now(timezone.utc)
    q = db.query(func.coalesce(func.sum(Transaction.amount), 0)).join(
        RecoveryAttempt, RecoveryAttempt.transaction_id == Transaction.id, isouter=True
    ).filter(
        Transaction.org_id == current_user.org_id,
        RecoveryAttempt.status == "completed",
        RecoveryAttempt.created_at >= start,
        RecoveryAttempt.created_at <= end,
    )
    total = q.scalar() or 0
    # Currency could be mixed; return raw total and count for simplicity
    count = db.query(func.count(RecoveryAttempt.id)).join(Transaction).filter(
        Transaction.org_id == current_user.org_id,
        RecoveryAttempt.status == "completed",
        RecoveryAttempt.created_at >= start,
        RecoveryAttempt.created_at <= end,
    ).scalar() or 0
    # Back-compat and console shape
    return {
        "total_recovered": int(total),
        "completed_count": int(count),
        "currency": "INR",
        "amount_cents": int(total),
        "from": start.isoformat(),
        "to": end.isoformat(),
    }


@router.get("/recovery_rate")
def recovery_rate(
    from_: Optional[str] = Query(None, alias="from"),
    to_: Optional[str] = Query(None, alias="to"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start = _parse_dt(from_) or datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = _parse_dt(to_) or datetime.now(timezone.utc)
    total = db.query(func.count(RecoveryAttempt.id)).join(Transaction).filter(
        Transaction.org_id == current_user.org_id,
        RecoveryAttempt.created_at >= start,
        RecoveryAttempt.created_at <= end,
    ).scalar() or 0
    completed = db.query(func.count(RecoveryAttempt.id)).join(Transaction).filter(
        Transaction.org_id == current_user.org_id,
        RecoveryAttempt.status == "completed",
        RecoveryAttempt.created_at >= start,
        RecoveryAttempt.created_at <= end,
    ).scalar() or 0
    pct = round((completed / total * 100.0), 2) if total else 0.0
    return {
        "recovery_rate": pct,
        "rate": round((completed / total), 4) if total else 0.0,
        "total_attempts": int(total),
        "completed": int(completed),
        "from": start.isoformat(),
        "to": end.isoformat(),
    }


@router.get("/attempts_summary")
def attempts_summary(
    from_: Optional[str] = Query(None, alias="from"),
    to_: Optional[str] = Query(None, alias="to"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start = _parse_dt(from_) or datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = _parse_dt(to_) or datetime.now(timezone.utc)
    # Group by status
    by_status = db.query(RecoveryAttempt.status, func.count(RecoveryAttempt.id)).join(Transaction).filter(
        Transaction.org_id == current_user.org_id,
        RecoveryAttempt.created_at >= start,
        RecoveryAttempt.created_at <= end,
    ).group_by(RecoveryAttempt.status).all()
    status_counts = {s or "unknown": int(c) for s, c in by_status}

    # Group by failure category (if recorded in FailureEvent.reason)
    by_cat = db.query(FailureEvent.reason, func.count(FailureEvent.id)).join(Transaction).filter(
        Transaction.org_id == current_user.org_id,
        FailureEvent.created_at >= start,
        FailureEvent.created_at <= end,
    ).group_by(FailureEvent.reason).all()
    category_counts = {cat or "unknown": int(c) for cat, c in by_cat}
    # Include by_channel key for console shape (not computed here)
    return {
        "by_status": status_counts,
        "by_category": category_counts,
        "by_channel": {},
        "from": start.isoformat(),
        "to": end.isoformat(),
    }


@router.get("/summary")
def summary(
    from_: Optional[str] = Query(None, alias="from"),
    to_: Optional[str] = Query(None, alias="to"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start = _parse_dt(from_) or datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = _parse_dt(to_) or datetime.now(timezone.utc)
    recovered_total = db.query(func.coalesce(func.sum(Transaction.amount), 0)).join(
        RecoveryAttempt, RecoveryAttempt.transaction_id == Transaction.id, isouter=True
    ).filter(
        Transaction.org_id == current_user.org_id,
        RecoveryAttempt.status == "completed",
        RecoveryAttempt.created_at >= start,
        RecoveryAttempt.created_at <= end,
    ).scalar() or 0
    # Simple failure breakdown across FailureEvent.reason
    by_cat = db.query(FailureEvent.reason, func.count(FailureEvent.id)).join(Transaction).filter(
        Transaction.org_id == current_user.org_id,
        FailureEvent.created_at >= start,
        FailureEvent.created_at <= end,
    ).group_by(FailureEvent.reason).all()
    failure = {cat or "other": int(c) for cat, c in by_cat}
    return {"recovered_amount_30d": int(recovered_total), "failure_categories": failure}


@router.get("/funnel")
def funnel(
    from_: Optional[str] = Query(None, alias="from"),
    to_: Optional[str] = Query(None, alias="to"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start = _parse_dt(from_) or datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = _parse_dt(to_) or datetime.now(timezone.utc)
    q_base = db.query(RecoveryAttempt).join(Transaction).filter(
        Transaction.org_id == current_user.org_id,
        RecoveryAttempt.created_at >= start,
        RecoveryAttempt.created_at <= end,
    )
    failed = db.query(func.count(RecoveryAttempt.id)).select_from(q_base.subquery()).scalar() or 0
    notified = db.query(func.count(RecoveryAttempt.id)).select_from(q_base.filter(RecoveryAttempt.status.in_(["sent", "opened", "completed"])) .subquery()).scalar() or 0
    clicked = db.query(func.count(RecoveryAttempt.id)).select_from(q_base.filter(RecoveryAttempt.status.in_(["opened", "completed"])) .subquery()).scalar() or 0
    paid = db.query(func.count(RecoveryAttempt.id)).select_from(q_base.filter(RecoveryAttempt.status == "completed").subquery()).scalar() or 0
    return {"failed": int(failed), "notified": int(notified), "clicked": int(clicked), "paid": int(paid)}
