from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db, get_current_user
from app.onboarding_models.onboarding import OnboardingStatus
from app.models import Organization, User

router = APIRouter(prefix="/v1/onboarding", tags=["Onboarding"])

@router.post("/finish")
def finish_onboarding(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    record = db.query(OnboardingStatus).filter(
        OnboardingStatus.user_id == user.user_id
    ).first()

    if not record or record.status != "credentials_saved":
        raise HTTPException(400, "Onboarding incomplete")

    # Create organization
    org = Organization(
        name=f"{user.email}-org",
        slug=user.email.split("@")[0],
        gateway=record.gateway,
        gateway_api_key=record.api_key,
        gateway_secret_key=record.secret_key
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    # Attach user to org
    user_row = db.query(User).filter(User.id == user.user_id).first()
    user_row.org_id = org.id
    db.commit()

    return {
        "message": "Onboarding complete",
        "next": "/dashboard/index.html"
    }
