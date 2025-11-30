from sqlalchemy.orm import Session
from app.models import AuditLog, User
from typing import Optional, Dict, Any

def log_audit(
    db: Session,
    org_id: int,
    user_id: Optional[int],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """
    Record an audit log entry for security and compliance.
    """
    try:
        log_entry = AuditLog(
            org_id=org_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        # Audit logging should not break the main flow, but we should log the error
        print(f"Failed to create audit log: {e}")
