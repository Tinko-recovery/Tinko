# app/routers/onboarding.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.deps import get_db, get_current_user
from app.onboarding_models.onboarding import OnboardingStatus

router = APIRouter()   # ❗ NO prefix here – prefix is added in main.py


class GatewaySelectRequest(BaseModel):
    gateway: str


class GatewaySelectResponse(BaseModel):
    message: str
    next: str


class OnboardingStatusResponse(BaseModel):
    status: str   # not_started / gateway_selected / credentials_completed / completed
    next: str     # where frontend should navigate next


@router.get("/status", response_model=OnboardingStatusResponse)
def get_onboarding_status(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    record = (
        db.query(OnboardingStatus)
        .filter(OnboardingStatus.user_id == user.user_id)
        .first()
    )

    # No record = never started onboarding
    if not record:
        return OnboardingStatusResponse(
            status="not_started",
            next="/onboarding/gateway",
        )

    # Fully done – existing customer → straight to dashboard
    if record.status == "completed":
        return OnboardingStatusResponse(
            status="completed",
            next="/dashboard",
        )

    # Map intermediate states to correct next step
    if record.status == "gateway_selected":
        return OnboardingStatusResponse(
            status="gateway_selected",
            next="/onboarding/credentials",
        )

    if record.status == "credentials_completed":
        return OnboardingStatusResponse(
            status="credentials_completed",
            next="/onboarding/finish",
        )

    # Fallback – treat unknown as start
    return OnboardingStatusResponse(
        status=record.status or "not_started",
        next="/onboarding/gateway",
    )


@router.post("/gateway", response_model=GatewaySelectResponse)
def select_gateway(
    payload: GatewaySelectRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    record = (
        db.query(OnboardingStatus)
        .filter(OnboardingStatus.user_id == user.user_id)
        .first()
    )

    if not record:
        record = OnboardingStatus(
            user_id=user.user_id,
            gateway=payload.gateway,
            status="gateway_selected",
        )
        db.add(record)
    else:
        # 👇 IMPORTANT: if already completed, don't silently reset
        if record.status == "completed":
            return GatewaySelectResponse(
                message="Onboarding already completed",
                next="/dashboard",
            )

        record.gateway = payload.gateway
        record.status = "gateway_selected"

    db.commit()

    return GatewaySelectResponse(
        message="Gateway saved successfully",
        next="/onboarding/credentials",
    )
