# app/routers/retry.py

from fastapi import APIRouter

router = APIRouter(tags=["retry"])

@router.get("/disabled")
def retry_disabled():
    return {
        "ok": False,
        "reason": "Retry engine is not active in this version of Tinko.",
        "action_required": "Background retry queue not implemented. Safe to ignore.",
    }
