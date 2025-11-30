from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db
from .. import models

router = APIRouter(tags=["recoveries"])


def _attempt_by_token(db: Session, token: str) -> Optional[models.RecoveryAttempt]:
    return db.query(models.RecoveryAttempt).filter(models.RecoveryAttempt.token == token).first()


def _as_aware_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    # If naive, treat as UTC; if aware, convert to UTC
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.get("/by_token/{token}")
def get_by_token(token: str, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    attempt = _attempt_by_token(db, token)
    if not attempt:
        return {"ok": False, "data": None, "error": {"code": "NOT_FOUND", "message": "Invalid or unknown link"}}

    # Expired
    expires_at = _as_aware_utc(attempt.expires_at)
    if expires_at and expires_at < now:
        return {"ok": False, "data": {"status": "expired"}, "error": {"code": "EXPIRED", "message": "Link has expired"}}

    # Used
    if attempt.used_at is not None:
        return {"ok": False, "data": {"status": "used"}, "error": {"code": "USED", "message": "Link already used"}}

    # Valid
    txn_ref = attempt.transaction_ref
    if not txn_ref and attempt.transaction_id:
        txn = db.query(models.Transaction).filter(models.Transaction.id == attempt.transaction_id).first()
        txn_ref = txn.transaction_ref if txn else None

    return {"ok": True, "data": {"transaction_ref": txn_ref, "status": attempt.status, "attempt_id": attempt.id}, "error": None}


@router.post("/by_token/{token}/open")
def mark_open(token: str, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    attempt = _attempt_by_token(db, token)
    if not attempt:
        return {"ok": False, "data": None, "error": {"code": "NOT_FOUND", "message": "Invalid or unknown link"}}

    # idempotent: only set if not set
    if attempt.opened_at is None:
        attempt.opened_at = now
        if attempt.status == "created":
            attempt.status = "opened"
        db.add(attempt)
        db.commit()

    return {"ok": True, "data": {"status": attempt.status, "opened_at": attempt.opened_at.isoformat() if attempt.opened_at else None}, "error": None}
