# app/routers/retry_policies.py

"""
API router for managing retry policies and monitoring retry status.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.deps import get_db, get_current_user
from app.models import (
    User,
    RetryPolicy,
    RecoveryAttempt,
    NotificationLog,
    Transaction,      # 👈 added for org filter in stats
)
from app.tasks.retry_tasks import update_retry_policy, schedule_retry  # (ok even if unused now)
from app.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Retry"])


# ----------------------------
# Pydantic Schemas
# ----------------------------

class RetryPolicyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    max_retries: int = Field(default=3, ge=1, le=10)
    initial_delay_minutes: int = Field(default=60, ge=1, le=1440)
    backoff_multiplier: int = Field(default=2, ge=1, le=5)
    max_delay_minutes: int = Field(default=1440, ge=60, le=10080)
    enabled_channels: List[str] = Field(default=["email"])
    # Optional alias for clients that send "channels"
    channels: Optional[List[str]] = None


class RetryPolicyResponse(BaseModel):
    id: int
    org_id: int
    name: str
    max_retries: int
    initial_delay_minutes: int
    backoff_multiplier: int
    max_delay_minutes: int
    enabled_channels: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RetryStatsResponse(BaseModel):
    total_attempts: int
    pending_retries: int
    sent_count: int
    completed_count: int
    failed_count: int
    avg_retry_count: float


class NotificationLogResponse(BaseModel):
    id: int
    channel: str
    recipient: str
    status: str
    provider: Optional[str]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    failed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ----------------------------
# Endpoints
# ----------------------------

@router.post("/policies", response_model=RetryPolicyResponse)
def create_retry_policy(
    policy_data: RetryPolicyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new retry policy for the organization.
    (RBAC can be added later; for now any logged-in user can create.)
    """
    # Deactivate existing active policies
    existing_policies = db.query(RetryPolicy).filter(
        RetryPolicy.org_id == current_user.org_id,
        RetryPolicy.is_active == True,
    ).all()

    for policy in existing_policies:
        policy.is_active = False

    # Determine channels (accept both enabled_channels and channels)
    channels = policy_data.enabled_channels or policy_data.channels or ["email"]

    # Create new policy
    new_policy = RetryPolicy(
        org_id=current_user.org_id,
        name=policy_data.name,
        max_retries=policy_data.max_retries,
        initial_delay_minutes=policy_data.initial_delay_minutes,
        backoff_multiplier=policy_data.backoff_multiplier,
        max_delay_minutes=policy_data.max_delay_minutes,
        enabled_channels=channels,
        is_active=True,
    )

    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)

    logger.info(
        "retry_policy_created",
        extra={
            "policy_id": new_policy.id,
            "org_id": current_user.org_id,
            "user_id": current_user.id,
        },
    )

    return new_policy


@router.get("/policies", response_model=List[RetryPolicyResponse])
def list_retry_policies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all retry policies for the current organization."""
    policies = (
        db.query(RetryPolicy)
        .filter(RetryPolicy.org_id == current_user.org_id)
        .order_by(RetryPolicy.created_at.desc())
        .all()
    )
    return policies


@router.get("/policies/active", response_model=Optional[RetryPolicyResponse])
def get_active_policy(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the currently active retry policy."""
    policy = db.query(RetryPolicy).filter(
        RetryPolicy.org_id == current_user.org_id,
        RetryPolicy.is_active == True,
    ).first()
    return policy


@router.delete("/policies/{policy_id}")
def deactivate_policy(
    policy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deactivate a retry policy."""
    policy = db.query(RetryPolicy).filter(
        RetryPolicy.id == policy_id,
        RetryPolicy.org_id == current_user.org_id,
    ).first()

    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    policy.is_active = False
    db.commit()

    logger.info(
        "retry_policy_deactivated",
        extra={
            "policy_id": policy_id,
            "org_id": current_user.org_id,
            "user_id": current_user.id,
        },
    )

    return {"message": "Policy deactivated"}


@router.get("/stats", response_model=RetryStatsResponse)
def get_retry_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get retry statistics for the organization.
    Filters attempts by current_user.org_id via Transaction.org_id.
    """
    attempts = (
        db.query(RecoveryAttempt)
        .join(Transaction, RecoveryAttempt.transaction_id == Transaction.id)
        .filter(Transaction.org_id == current_user.org_id)
        .all()
    )

    total = len(attempts)
    pending = sum(1 for a in attempts if a.status in ["created", "sent"])
    sent = sum(1 for a in attempts if a.status == "sent")
    completed = sum(1 for a in attempts if a.status == "completed")
    failed = sum(1 for a in attempts if a.status in ["expired", "cancelled"])
    avg_retries = sum(a.retry_count for a in attempts) / max(total, 1)

    return RetryStatsResponse(
        total_attempts=total,
        pending_retries=pending,
        sent_count=sent,
        completed_count=completed,
        failed_count=failed,
        avg_retry_count=round(avg_retries, 2),
    )


@router.get(
    "/attempts/{attempt_id}/notifications",
    response_model=List[NotificationLogResponse],
)
def get_attempt_notifications(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all notification logs for a specific recovery attempt."""
    attempt = db.query(RecoveryAttempt).filter(
        RecoveryAttempt.id == attempt_id
    ).first()

    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    notifications = (
        db.query(NotificationLog)
        .filter(NotificationLog.recovery_attempt_id == attempt_id)
        .order_by(NotificationLog.created_at.desc())
        .all()
    )

    return notifications


@router.post("/attempts/{attempt_id}/retry-now")
def trigger_immediate_retry(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Trigger an immediate retry for a recovery attempt.
    (RBAC can be enforced later; currently any logged-in user.)
    """
    attempt = db.query(RecoveryAttempt).filter(
        RecoveryAttempt.id == attempt_id
    ).first()

    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.retry_count >= attempt.max_retries:
        raise HTTPException(status_code=400, detail="Max retries exceeded")

    # Try sending notification via Celery (if configured)
    try:
        from app.tasks.notification_tasks import send_recovery_notification

        send_recovery_notification.delay(attempt_id)
    except Exception as e:
        logger.warning("celery_unavailable_skip", extra={"error": str(e)})

    logger.info(
        "immediate_retry_triggered",
        extra={
            "attempt_id": attempt_id,
            "user_id": current_user.id,
            "org_id": current_user.org_id,
        },
    )

    return {"message": "Retry triggered", "attempt_id": attempt_id}
