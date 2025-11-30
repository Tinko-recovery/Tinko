from sqlalchemy import Column, String
from app.db import Base

class OnboardingStatus(Base):
    __tablename__ = "onboarding_status"

    user_id = Column(String, primary_key=True, index=True)
    gateway = Column(String, nullable=True)
    api_key = Column(String, nullable=True)
    secret_key = Column(String, nullable=True)
    status = Column(String, default="started", nullable=False)
