from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models import User

router = APIRouter(tags=["Admin DB"])


@router.get("/stats")
def get_db_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simple DB stats endpoint.
    Only requires authenticated dashboard user.
    """

    # Optional: Restrict only yourself (founder)
    # if current_user.email != "sadish@tinko.in":
    #     raise HTTPException(403, "Not allowed")

    try:
        user_count = db.execute("SELECT COUNT(*) FROM users").scalar()
    except Exception:
        user_count = "N/A"

    return {
        "db_status": "ok",
        "user_count": user_count
    }
