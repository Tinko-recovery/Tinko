"""
Analytics service for recovery metrics and insights.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models import RecoveryAttempt, Transaction, FailureEvent

def get_recovery_rate(db: Session, org_id: int, days: int = 30) -> dict:
    """Calculate recovery rate percentage."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    total = db.query(func.count(RecoveryAttempt.id)).filter(
        RecoveryAttempt.created_at >= cutoff
    ).scalar() or 0
    
    successful = db.query(func.count(RecoveryAttempt.id)).filter(
        RecoveryAttempt.created_at >= cutoff,
        RecoveryAttempt.status == "completed"
    ).scalar() or 0
    
    rate = (successful / total * 100) if total > 0 else 0
    
    return {
        "total_attempts": total,
        "successful": successful,
        "recovery_rate": round(rate, 2),
        "period_days": days
    }

def get_failure_categories(db: Session, org_id: int) -> list:
    """Get failure event categories breakdown."""
    results = db.query(
        FailureEvent.reason,
        func.count(FailureEvent.id).label('count')
    ).group_by(FailureEvent.reason).all()
    
    return [{"category": r.reason, "count": r.count} for r in results]

def get_revenue_recovered(db: Session, org_id: int, days: int = 30) -> dict:
    """Calculate total revenue recovered."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    total = db.query(func.sum(Transaction.amount)).join(
        RecoveryAttempt
    ).filter(
        RecoveryAttempt.status == "completed",
        RecoveryAttempt.created_at >= cutoff
    ).scalar() or 0
    
    return {
        "total_recovered": total,
        "currency": "usd",
        "period_days": days
    }

def get_attempts_by_channel(db: Session, org_id: int) -> list:
    """Get recovery attempts breakdown by channel."""
    results = db.query(
        RecoveryAttempt.channel,
        func.count(RecoveryAttempt.id).label('count')
    ).group_by(RecoveryAttempt.channel).all()
    
    return [{"channel": r.channel or "link", "count": r.count} for r in results]
