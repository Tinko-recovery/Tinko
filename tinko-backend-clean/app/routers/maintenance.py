from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.models import User

router = APIRouter(tags=["Maintenance"])


@router.get("/ping")
def maintenance_ping(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Simple maintenance endpoint.
    Used mainly to verify app health with authenticated access.
    """
    return {
        "status": "ok",
        "message": "Maintenance route reachable",
        "user": current_user.email,
    }
