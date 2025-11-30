from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class RecoveryLinkOut(BaseModel):
    recovery_id: str
    transaction_ref: str
    token: str
    link_url: str
    attempt_count: int
    next_retry_at: Optional[datetime]
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class RecoveryAttemptOut(BaseModel):
    attempt_id: str
    recovery_id: str
    attempt_number: int
    status: str
    sent_via: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class RecoveryLinkRequest(BaseModel):
    transaction_ref: str


class RecoveryAttemptsResponse(BaseModel):
    recovery: RecoveryLinkOut
    attempts: List[RecoveryAttemptOut]
