import os, json, uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from .storage import DB
from .rules import classify_failure, next_retry_options

app = FastAPI(title="Tinko Recovery")

# Prefer Neon Postgres via DATABASE_URL; fall back to legacy TINKO_DB_URL only if provided.
db_url = os.getenv("DATABASE_URL") or os.getenv("TINKO_DB_URL") or ""
if not db_url:
    raise RuntimeError(
        "DATABASE_URL must be set (Neon Postgres). Provide it in .env or the environment."
    )
db = DB(db_url)
db.init()

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/webhook/payment")
async def payment_webhook(req: Request):
    try:
        payload = await req.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    event_id     = payload.get("event_id") or str(uuid.uuid4())
    event_type   = payload.get("event_type") or "payment_failed"
    order_id     = payload.get("order_id")
    attempt_id   = payload.get("attempt_id")
    customer_id  = (payload.get("customer") or {}).get("id")
    amount       = int(payload.get("amount", 0))
    currency     = payload.get("currency", "INR")
    status       = payload.get("status", "failed")
    failure_code = (payload.get("failure") or {}).get("code")
    failure_msg  = (payload.get("failure") or {}).get("message")

    if not order_id:
        raise HTTPException(400, "order_id required")

    try:
        db.insert_event(
            id=event_id, order_id=order_id, attempt_id=attempt_id, customer_id=customer_id,
            event_type=event_type, status=status, failure_code=failure_code, failure_message=failure_msg,
            amount=amount, currency=currency, raw_json=json.dumps(payload),
        )
    except Exception as e:
        # Unique constraint message text varies slightly by driver
        if "UNIQUE" in str(e).upper() and "EVENTS" in str(e).upper():
            return JSONResponse({"ok": True, "duplicate": True})
        raise

    advice = None
    if status == "failed":
        category = classify_failure(failure_code, failure_msg)
        advice = next_retry_options(category)

    return {"ok": True, "advice": advice}

@app.post("/attempts")
async def create_attempt(req: Request):
    body = await req.json()
    attempt_id = str(uuid.uuid4())
    db.insert_attempt(
        id=attempt_id, order_id=body["order_id"], attempt_from_event=body["from_event"],
        method=body["method"], strategy=body["strategy"], status="initiated",
    )
    return {"ok": True, "attempt_id": attempt_id}
