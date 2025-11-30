from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..deps import get_db
from .. import models, schemas
import os

router = APIRouter(tags=["recoveries"])
bearer_optional = HTTPBearer(auto_error=False)

BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000")

@router.post("/by_ref/{transaction_ref}/link", response_model=schemas.RecoveryLinkOut, status_code=status.HTTP_201_CREATED)
def create_link_by_ref(transaction_ref: str, body: schemas.RecoveryLinkRequest = schemas.RecoveryLinkRequest(), db: Session = Depends(get_db)):
    txn = db.query(models.Transaction).filter(models.Transaction.transaction_ref == transaction_ref).first()
    if txn is None:
        raise HTTPException(status_code=404, detail="transaction_ref not found")

    token = token_urlsafe(16)  # ~22-char URL-safe
    expires_at = datetime.now(timezone.utc) + timedelta(hours=body.ttl_hours)

    # Validate channel
    valid_channels = {"email", "sms", "whatsapp"}
    requested_channel = body.channel or "email"
    if requested_channel not in valid_channels:
        raise HTTPException(status_code=400, detail=f"Invalid channel. Must be one of {valid_channels}")

    attempt = models.RecoveryAttempt(
        transaction_id=txn.id,
        channel=requested_channel,
        token=token,
        status="created",
        expires_at=expires_at,
    )
    db.add(attempt); db.commit(); db.refresh(attempt)
    # Enqueue initial retry schedule based on active policy
    try:
        from app.tasks.retry_tasks import schedule_retry
        # Use org_id from transaction if available for policy lookup
        schedule_retry(attempt.id, getattr(txn, 'org_id', None))
    except Exception as e:
        # Log error but don't fail request
        print(f"Retry schedule failed: {e}")
        pass

    url = f"{BASE_URL}/pay/retry/{token}"
    return {
        "attempt_id": attempt.id,
        "transaction_id": txn.id,
        "token": token,
        "url": url,
        "expires_at": expires_at.isoformat(),
    }

@router.get("/by_ref/{transaction_ref}")
def list_attempts_by_ref(transaction_ref: str, db: Session = Depends(get_db)):
    txn = db.query(models.Transaction).filter(models.Transaction.transaction_ref == transaction_ref).first()
    if txn is None:
        return []
    rows = (
        db.query(models.RecoveryAttempt)
        .filter(models.RecoveryAttempt.transaction_id == txn.id)
        .order_by(models.RecoveryAttempt.id.desc())
        .all()
    )
    out = []
    for r in rows:
        out.append({
            "attempt_id": r.id,
            "transaction_id": r.transaction_id,
            "channel": r.channel,
            "token": r.token,
            "status": r.status,
            "expires_at": r.expires_at.isoformat() if r.expires_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "used_at": r.used_at.isoformat() if r.used_at else None,
            "url": f"{os.getenv('PUBLIC_BASE_URL','http://127.0.0.1:8000')}/pay/retry/{r.token}",
        })
    return out


@router.patch("/{recovery_id}/next_retry_at")
def update_next_retry_at(
    recovery_id: int,
    body: schemas.NextRetryAtPatch,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_optional),
):
    """Update the next_retry_at for a recovery attempt.

    Authorization:
    - Operator/Admin bearer JWT (org must own the transaction)
    - OR Recovery link bearer token (raw token created for the attempt)
    """
    # Parse desired datetime
    try:
        desired_dt = datetime.fromisoformat(body.next_retry_at.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid next_retry_at format; must be ISO8601")

    now = datetime.now(timezone.utc)
    if desired_dt.tzinfo is None:
        # Assume UTC if no tz provided
        desired_dt = desired_dt.replace(tzinfo=timezone.utc)
    if desired_dt <= now:
        raise HTTPException(status_code=400, detail="next_retry_at must be in the future (UTC)")

    attempt = db.query(models.RecoveryAttempt).filter(models.RecoveryAttempt.id == recovery_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="recovery_id not found")

    # Status validation
    allowed_status = {"created", "sent", "scheduled"}
    if attempt.status not in allowed_status:
        raise HTTPException(status_code=409, detail=f"Cannot update in status '{attempt.status}'. Allowed: {sorted(allowed_status)}")

    # Authorization: either user JWT (operator/admin) with same org, or recovery token matching this attempt
    authorized = False
    if credentials and credentials.credentials:
        token = credentials.credentials
        from app.security import decode_jwt
        payload = decode_jwt(token)
        if payload and (role := payload.get("role")) in ("operator", "admin"):
            # Ensure user/org owns the transaction (if present)
            user_org_id = payload.get("org_id")
            txn = attempt.transaction
            if txn is None or (user_org_id is not None and txn.org_id == user_org_id):
                authorized = True
            else:
                raise HTTPException(status_code=403, detail="Forbidden: attempt does not belong to your org")
        else:
            # Treat token as recovery link token
            if token == attempt.token and attempt.expires_at and attempt.expires_at > now:
                authorized = True

    if not authorized:
        raise HTTPException(status_code=401, detail="Unauthorized: provide operator/admin JWT or valid recovery token")

    # Update
    attempt.next_retry_at = desired_dt
    # Optionally flip status to scheduled if still created/sent
    if attempt.status in {"created", "sent"}:
        attempt.status = "scheduled"
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return {
        "attempt_id": attempt.id,
        "next_retry_at": attempt.next_retry_at.isoformat() if attempt.next_retry_at else None,
        "status": attempt.status,
    }
