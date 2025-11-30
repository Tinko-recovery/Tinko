from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict


# ------------------------------------------------------
# CUSTOMER
# ------------------------------------------------------

class CustomerIn(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None


# ------------------------------------------------------
# FAILURE EVENT
# ------------------------------------------------------

class FailureEventIn(BaseModel):
    transaction_ref: str = Field(..., min_length=1, max_length=64)
    amount: Optional[int] = Field(None, ge=0, description="minor units (e.g., paise)")
    currency: Optional[str] = Field(None, min_length=3, max_length=8)
    gateway: Optional[str] = None
    failure_reason: str = Field(..., min_length=1)
    occurred_at: Optional[str] = None  # ISO 8601 datetime string
    metadata: Optional[Dict[str, Any]] = None
    customer: Optional[CustomerIn] = None


class FailureEventOut(BaseModel):
    id: int
    transaction_id: int

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------
# RECOVERY LINK
# ------------------------------------------------------

class RecoveryLinkRequest(BaseModel):
    """Request from /v1/recoveries/by_ref/{transaction_ref}/link"""
    ttl_hours: float = Field(default=24, ge=0, le=168)
    channel: Optional[str] = "link"


class RecoveryLinkOut(BaseModel):
    """Response containing the generated recovery link"""
    attempt_id: int
    transaction_id: int
    token: str
    url: str
    expires_at: str  # ISO8601


# ------------------------------------------------------
# RECOVERY ATTEMPT + PATCH
# ------------------------------------------------------

class NextRetryAtPatch(BaseModel):
    """Payload for PATCH /recoveries/{recovery_id}/next_retry_at"""
    next_retry_at: str = Field(
        ...,
        description="ISO8601 UTC timestamp when the next retry should occur"
    )


class RecoveryAttemptOut(BaseModel):
    """Attempt record details"""
    attempt_id: int
    recovery_id: int
    attempt_number: int
    status: str
    sent_via: str
    created_at: str  # ISO8601


class RecoveryAttemptsResponse(BaseModel):
    """Combined response containing recovery + all attempts"""
    recovery: RecoveryLinkOut
    attempts: List[RecoveryAttemptOut]


# ------------------------------------------------------
# OPTIONAL: make these importable via schemas.RecoveryLinkOut etc.
# ------------------------------------------------------

__all__ = [
    # Failure events
    "CustomerIn",
    "FailureEventIn",
    "FailureEventOut",

    # Recovery link
    "RecoveryLinkRequest",
    "RecoveryLinkOut",

    # Retry patch
    "NextRetryAtPatch",

    # Attempts
    "RecoveryAttemptOut",
    "RecoveryAttemptsResponse",
]
