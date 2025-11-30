# app/tasks/retry_tasks.py

"""
Lightweight placeholder retry task module.
This exists because older routers import from app.tasks.retry_tasks.
We no longer use Celery, so all functions run synchronously.

Later you can plug in:
 - Supabase Edge Functions
 - Cron triggers
 - n8n retry pipeline
 - In-process scheduler
"""

import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# PROCESS RETRY QUEUE (used by router /v1/retry/trigger-due)
# ---------------------------------------------------------
def process_retry_queue():
    """
    Placeholder retry queue processor.
    Returns a simple status message.
    """
    logger.info("Retry queue processing started (stub).")

    # In the future: read pending retries from DB and process them.
    processed = 0

    logger.info("Retry queue processing finished (stub).")

    return {
        "message": "Retry queue processed (stub version).",
        "processed": processed
    }


# ---------------------------------------------------------
# UPDATE RETRY POLICY (used by retry_policies router)
# ---------------------------------------------------------
def update_retry_policy(policy_id: int, data: dict):
    """
    Stub: Update retry policy configuration.
    """
    logger.info(f"Updating retry policy (stub): {policy_id}")
    return {
        "message": "Retry policy update not implemented.",
        "policy_id": policy_id,
        "received_data": data
    }


# ---------------------------------------------------------
# SCHEDULE RETRY (used internally by recovery pipeline)
# ---------------------------------------------------------
from app.services.task_queue import register_task, enqueue_job

# ---------------------------------------------------------
# SCHEDULE RETRY (used internally by recovery pipeline)
# ---------------------------------------------------------

@register_task("execute_retry_attempt")
def execute_retry_attempt_task(attempt_id: int, org_id: int = None):
    """
    Execute retry attempt: Send recovery link via configured channel.
    """
    logger.info(f"Processing retry for attempt_id={attempt_id}")
    
    from app.db import SessionLocal
    from app import models
    from app.services.email_service import send_email
    from app.services.sms_service import send_recovery_sms
    import os

    db = SessionLocal()
    try:
        attempt = db.query(models.RecoveryAttempt).filter(models.RecoveryAttempt.id == attempt_id).first()
        if not attempt:
            logger.error(f"Attempt {attempt_id} not found")
            return

        txn = attempt.transaction
        if not txn:
            logger.error(f"Transaction for attempt {attempt_id} not found")
            return

        # Generate Link
        base_url = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000")
        recovery_link = f"{base_url}/pay/retry/{attempt.token}"
        
        # Prepare Data
        amount_fmt = f"{txn.currency} {txn.amount/100:.2f}" if txn.amount else "Unknown Amount"
        merchant_name = txn.organization.name if txn.organization else "Tinko Merchant"
        
        # Send Notification
        success = False
        error_msg = None
        
        # Determine channels to use
        # Use Organization settings, fallback to attempt.channel
        channels = txn.organization.recovery_channels if txn.organization and txn.organization.recovery_channels else [attempt.channel]
        
        # Send Notifications
        results = {}
        
        # 1. EMAIL
        if "email" in channels and txn.customer_email:
            try:
                link_email = f"{recovery_link}?channel=email"
                html_content = f"""
                <div style="font-family: sans-serif; padding: 20px;">
                    <h2>Payment Failed</h2>
                    <p>Hi,</p>
                    <p>Your payment of <strong>{amount_fmt}</strong> to <strong>{merchant_name}</strong> failed.</p>
                    <p>You can retry the payment securely using the link below:</p>
                    <a href="{link_email}" style="background: #DE6B06; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Retry Payment</a>
                    <p style="margin-top: 20px; font-size: 12px; color: #666;">Link expires in 24 hours.</p>
                </div>
                """
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                loop.run_until_complete(send_email(
                    to_email=txn.customer_email,
                    subject=f"Action Required: Payment to {merchant_name} Failed",
                    text=f"Retry your payment here: {link_email}",
                    html=html_content
                ))
                results["email"] = "sent"
            except Exception as e:
                logger.error(f"Email send failed: {e}")
                results["email"] = f"failed: {e}"

        # 2. SMS
        if "sms" in channels and txn.customer_phone:
            try:
                link_sms = f"{recovery_link}?channel=sms"
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                res = loop.run_until_complete(send_recovery_sms(
                    mobile_number=txn.customer_phone,
                    recovery_link=link_sms,
                    amount=amount_fmt,
                    merchant=merchant_name,
                    channel="sms"
                ))
                if res.get("success"):
                    results["sms"] = "sent"
                else:
                    results["sms"] = f"failed: {res.get('error')}"
            except Exception as e:
                logger.error(f"SMS send failed: {e}")
                results["sms"] = f"failed: {e}"

        # 3. WHATSAPP
        if "whatsapp" in channels and txn.customer_phone:
            try:
                link_wa = f"{recovery_link}?channel=whatsapp"
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # Assuming send_recovery_sms handles 'whatsapp' channel arg correctly
                res = loop.run_until_complete(send_recovery_sms(
                    mobile_number=txn.customer_phone,
                    recovery_link=link_wa,
                    amount=amount_fmt,
                    merchant=merchant_name,
                    channel="whatsapp"
                ))
                if res.get("success"):
                    results["whatsapp"] = "sent"
                else:
                    results["whatsapp"] = f"failed: {res.get('error')}"
            except Exception as e:
                logger.error(f"WhatsApp send failed: {e}")
                results["whatsapp"] = f"failed: {e}"
        
        # Update Attempt Status
        # If at least one sent, mark as sent
        if any(v == "sent" for v in results.values()):
            attempt.status = "sent"
        
        # Log Notifications (One log per channel)
        for ch, status in results.items():
            log = models.NotificationLog(
                recovery_attempt_id=attempt.id,
                channel=ch,
                recipient=txn.customer_email if ch == "email" else txn.customer_phone,
                status="sent" if status == "sent" else "failed",
                error_message=status if status != "sent" else None
            )
            db.add(log)
        
        db.commit()

    except Exception as e:
        logger.error(f"Retry task error: {e}")
    finally:
        db.close()

def schedule_retry(attempt_id: int, org_id: int = None, delay_minutes: int = 0):
    """
    Enqueue the retry attempt.
    """
    job_id = enqueue_job("execute_retry_attempt", {"attempt_id": attempt_id, "org_id": org_id}, delay_minutes=delay_minutes)
    logger.info(f"Retry attempt {attempt_id} enqueued: Job {job_id} (delay={delay_minutes}m)")
    return job_id
