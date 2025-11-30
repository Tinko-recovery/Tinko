# app/services/onboarding_service.py

from sqlalchemy.orm import Session
from app.onboarding_models.onboarding import OnboardingStatus


class OnboardingService:

    @staticmethod
    def set_gateway(db: Session, user_id: str, gateway: str):
        record = db.query(OnboardingStatus).filter(
            OnboardingStatus.user_id == user_id
        ).first()

        if not record:
            record = OnboardingStatus(
                user_id=user_id,
                gateway=gateway,
                status="gateway_selected"
            )
            db.add(record)
        else:
            record.gateway = gateway
            record.status = "gateway_selected"

        db.commit()
