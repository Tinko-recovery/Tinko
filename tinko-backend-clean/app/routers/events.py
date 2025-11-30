from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional

from ..deps import get_db
from .. import models, schemas
from ..services.classifier import classify_event
from ..security import decode_jwt

router = APIRouter(tags=["events"])

@router.post("/payment_failed", response_model=schemas.FailureEventOut, status_code=status.HTTP_201_CREATED)
def payment_failed(
    payload: schemas.FailureEventIn, 
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    # Check for duplicate idempotency key
    if idempotency_key:
        existing = db.query(models.FailureEvent).filter(
            models.FailureEvent.meta.contains({"idempotency_key": idempotency_key})
        ).first()
        if existing:
            return existing
    
    # Upsert transaction by external reference
    txn = db.query(models.Transaction).filter(models.Transaction.transaction_ref == payload.transaction_ref).first()
    if txn is None:
        txn = models.Transaction(
            transaction_ref=payload.transaction_ref,
            amount=payload.amount,
            currency=payload.currency,
        )
        db.add(txn); db.flush()
    else:
        if payload.amount is not None: txn.amount = payload.amount
        if payload.currency is not None: txn.currency = payload.currency

    # Guardrail A: If Authorization is present, assign transaction to the user's org
    try:
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1]
            payload_jwt = decode_jwt(token)
            if payload_jwt and (user_id := payload_jwt.get("user_id")):
                user = db.query(models.User).filter(models.User.id == user_id).first()
                if user and user.org_id:
                    txn.org_id = user.org_id
    except Exception:
        # Never block ingest due to auth parsing issues
        pass

    # Parse occurred_at if provided (ISO 8601)
    occurred = None
    if payload.occurred_at:
        try:
            occurred = datetime.fromisoformat(payload.occurred_at.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid occurred_at. Use ISO-8601 (e.g., 2025-10-07T14:25:00Z).")

    # Build meta: prefer explicit payload.metadata; also keep any extra fields
    extras = payload.model_dump(exclude={"transaction_ref","amount","currency","gateway","failure_reason","occurred_at","metadata"})
    combined_meta = {}
    if payload.metadata: combined_meta["metadata"] = payload.metadata
    if extras: combined_meta["extras"] = extras
    if idempotency_key: combined_meta["idempotency_key"] = idempotency_key
    # Optional: persist classifier category for analytics/routing
    try:
        clf = classify_event(getattr(payload, 'gateway', None), getattr(payload, 'failure_reason', None))
        if clf and clf.get('category'):
            combined_meta["category"] = clf['category']
    except Exception:
        pass

    fe = models.FailureEvent(
        transaction_id=txn.id,
        gateway=payload.gateway,
        reason=payload.failure_reason,
        meta=combined_meta or None,
        occurred_at=occurred,
    )
    db.add(fe); db.commit(); db.refresh(fe)
    return fe

@router.get("/by_ref/{transaction_ref}")
def list_events_by_ref(transaction_ref: str, db: Session = Depends(get_db)):
    txn = db.query(models.Transaction).filter(models.Transaction.transaction_ref == transaction_ref).first()
    if txn is None:
        return []
    rows = (
        db.query(models.FailureEvent)
        .filter(models.FailureEvent.transaction_id == txn.id)
        .order_by(models.FailureEvent.id.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "transaction_id": r.transaction_id,
            "gateway": r.gateway,
            "reason": r.reason,
            "occurred_at": r.occurred_at.isoformat() if r.occurred_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "meta": r.meta,
        } for r in rows
    ]
