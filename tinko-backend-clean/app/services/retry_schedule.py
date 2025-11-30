from datetime import datetime, timedelta, timezone
from typing import Optional


class RetryPolicyLike:
    """Minimal policy shape for scheduling computation."""
    initial_delay_minutes: int
    backoff_multiplier: int
    max_delay_minutes: int


def compute_retry_schedule(
    policy: RetryPolicyLike,
    now: Optional[datetime],
    attempt_index: int,
) -> datetime:
    """Compute next retry datetime using exponential backoff with cap.

    Args:
        policy: Object with initial_delay_minutes, backoff_multiplier, max_delay_minutes
        now: Base time; if None, uses current UTC
        attempt_index: 0-based retry index (0 for first retry)

    Returns:
        datetime in UTC for the next retry
    """
    if now is None:
        now = datetime.now(timezone.utc)
    else:
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

    # Exponential backoff
    delay_minutes = policy.initial_delay_minutes * (policy.backoff_multiplier ** attempt_index)
    # Cap at max_delay_minutes
    delay_minutes = min(delay_minutes, policy.max_delay_minutes)
    return now + timedelta(minutes=delay_minutes)
