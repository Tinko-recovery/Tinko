from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, Query, Depends

try:
    from app.deps import require_org  # type: ignore
except Exception:
    def require_org():  # fallback for local smoke
        return {"org_id": "local-smoke"}

router = APIRouter(tags=["schedule"])


@router.get("/suggested_windows")
def suggested_windows(
    ref: str = Query(...),
    hours_ahead: int = Query(48, ge=1, le=168),
    _org: Any = Depends(require_org),
) -> Dict[str, Any]:
    """Suggest top-of-hour 30m windows for the next N hours with a dummy score."""
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    slots: List[Dict[str, Any]] = []
    for i in range(min(hours_ahead, 8)):
        start = now + timedelta(hours=i + 1)
        end = start + timedelta(minutes=30)
        slots.append({
            "start": start.isoformat().replace("+00:00", "Z"),
            "end": end.isoformat().replace("+00:00", "Z"),
            "score": round(0.8 - i * 0.03, 2),
        })
    return {"ref": ref, "slots": slots, "hours_ahead": hours_ahead}
