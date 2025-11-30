import logging
import traceback
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import WebhookEvent
from app.db import SessionLocal

logger = logging.getLogger(__name__)

def log_webhook(provider: str, headers: dict, payload: dict, db: Session = None) -> WebhookEvent:
    """
    Log a raw webhook event to the database.
    Returns the WebhookEvent object.
    """
    close_db = False
    if not db:
        db = SessionLocal()
        close_db = True
        
    try:
        event = WebhookEvent(
            provider=provider,
            headers=headers,
            payload=payload,
            status="received"
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    except Exception as e:
        logger.error(f"Failed to log webhook: {e}")
        # We should try to log this to a file or stderr at least
        return None
    finally:
        if close_db:
            db.close()

def update_webhook_status(event_id: int, status: str, error: str = None, db: Session = None):
    """
    Update the status of a webhook event.
    """
    close_db = False
    if not db:
        db = SessionLocal()
        close_db = True
        
    try:
        event = db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
        if event:
            event.status = status
            event.processed_at = datetime.utcnow()
            if error:
                event.error = error
            db.commit()
    except Exception as e:
        logger.error(f"Failed to update webhook status: {e}")
    finally:
        if close_db:
            db.close()
