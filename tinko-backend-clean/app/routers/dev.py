# app/routers/dev.py  (append)
from app.db import engine, SessionLocal
from sqlalchemy import text
from fastapi import APIRouter
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
import os

from .. import models

router = APIRouter(tags=["_dev"])

@router.post("/bootstrap/recoveries")
def bootstrap_recoveries():
    sql = """
    CREATE TABLE IF NOT EXISTS recoveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER NOT NULL,
        token TEXT NOT NULL,
        url TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        opened_at TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(transaction_id) REFERENCES transactions(id)
    );
    """
    with engine.connect() as conn:
        conn.exec_driver_sql(sql)
    return {"ok": True, "created_or_exists": "recoveries"}

@router.get("/schema/recoveries")
def schema_recoveries():
    with engine.connect() as conn:
        rows = conn.exec_driver_sql("PRAGMA table_info(recoveries)").all()
    return [{"cid": r[0], "name": r[1], "type": r[2], "notnull": r[3], "dflt": r[4]} for r in rows]


@router.post("/seed/transaction")
def seed_transaction(ref: str = "ref_demo_1", amount: int = 1999, currency: str = "inr"):
    db = SessionLocal()
    try:
        txn = db.query(models.Transaction).filter(models.Transaction.transaction_ref == ref).first()
        if not txn:
            txn = models.Transaction(transaction_ref=ref, amount=amount, currency=currency)
            db.add(txn)
            db.commit()
            db.refresh(txn)
        return {"ok": True, "id": txn.id, "transaction_ref": txn.transaction_ref, "amount": txn.amount, "currency": txn.currency}
    finally:
        db.close()


@router.post("/seed/recovery_link")
def seed_recovery_link(ref: str = "ref_demo_1", ttl_hours: float = 24.0):
    db = SessionLocal()
    try:
        txn = db.query(models.Transaction).filter(models.Transaction.transaction_ref == ref).first()
        if not txn:
            txn = models.Transaction(transaction_ref=ref, amount=1999, currency="inr")
            db.add(txn)
            db.commit()
            db.refresh(txn)

        token = token_urlsafe(16)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        attempt = models.RecoveryAttempt(
            transaction_id=txn.id,
            transaction_ref=txn.transaction_ref,
            channel="link",
            token=token,
            status="created",
            expires_at=expires_at,
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        base = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000")
        url = f"{base}/pay/retry/{token}"
        return {"ok": True, "attempt_id": attempt.id, "token": token, "url": url, "expires_at": expires_at.isoformat(), "transaction_ref": txn.transaction_ref}
    finally:
        db.close()
