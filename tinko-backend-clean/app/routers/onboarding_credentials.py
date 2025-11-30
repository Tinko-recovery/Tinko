from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.deps import get_db, get_current_user
from app.onboarding_models.onboarding import OnboardingStatus

router = APIRouter(prefix="/v1/onboarding", tags=["Onboarding"])

class CredentialsRequest(BaseModel):
    api_key: str
    secret_key: str

class CredentialsResponse(BaseModel):
    message: str
    next: str

@router.post("/credentials", response_model=CredentialsResponse)
def save_credentials(
    payload: CredentialsRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    record = db.query(OnboardingStatus).filter(
        OnboardingStatus.user_id == user.user_id
    ).first()

    if not record:
        raise HTTPException(400, "Gateway not selected yet")

    record.api_key = payload.api_key
    record.secret_key = payload.secret_key
    record.status = "credentials_saved"

    db.commit()

    return CredentialsResponse(
        message="Credentials saved",
        next="/onboarding/finish"
    )
