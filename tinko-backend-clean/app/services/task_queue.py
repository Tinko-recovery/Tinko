import logging
import traceback
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Job

logger = logging.getLogger(__name__)

# Registry of available tasks
TASK_REGISTRY = {}

def register_task(name):
    """Decorator to register a function as a task."""
    def decorator(func):
        TASK_REGISTRY[name] = func
        return func
    return decorator

def enqueue_job(task_name: str, args: dict = None, delay_minutes: int = 0, db: Session = None):
    """
    Add a job to the queue.
    """
    if args is None:
        args = {}
    
    scheduled_at = datetime.utcnow() + timedelta(minutes=delay_minutes)
    
    job = Job(
        task_name=task_name,
        arguments=args,
        scheduled_at=scheduled_at,
        status="pending"
    )
    
    # Use provided session or create new one
    close_db = False
    if not db:
        db = SessionLocal()
        close_db = True
        
    try:
        db.add(job)
        db.commit()
        db.refresh(job)
        logger.info(f"Job {job.id} enqueued: {task_name} at {scheduled_at}")
        return job.id
    except Exception as e:
        logger.error(f"Failed to enqueue job: {e}")
        db.rollback()
        return None
    finally:
        if close_db:
            db.close()

def run_pending_jobs(limit=10):
    """
    Fetch and run pending jobs.
    This should be called by a background worker or cron.
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        
        # Fetch pending jobs that are due
        # Note: In a distributed system, you'd need row locking (SELECT FOR UPDATE SKIP LOCKED)
        # For this single-instance setup, this is acceptable.
        jobs = db.query(Job).filter(
            Job.status == "pending",
            Job.scheduled_at <= now
        ).order_by(Job.scheduled_at.asc()).limit(limit).all()
        
        if not jobs:
            return 0
            
        logger.info(f"Found {len(jobs)} pending jobs")
        
        for job in jobs:
            process_job(db, job)
            
        return len(jobs)
    finally:
        db.close()

def process_job(db: Session, job: Job):
    """
    Execute a single job.
    """
    logger.info(f"Processing Job {job.id}: {job.task_name}")
    
    # Mark as running
    job.status = "running"
    job.started_at = datetime.utcnow()
    db.commit()
    
    try:
        task_func = TASK_REGISTRY.get(job.task_name)
        if not task_func:
            raise ValueError(f"Task {job.task_name} not registered")
            
        # Execute
        # We assume arguments match the function signature
        task_func(**job.arguments)
        
        # Success
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        logger.info(f"Job {job.id} completed successfully")
        
    except Exception as e:
        # Failure
        logger.error(f"Job {job.id} failed: {e}")
        job.status = "failed"
        job.error = str(e) + "\n" + traceback.format_exc()
        
        # Simple Retry Logic (Optional Phase 2)
        # if job.retry_count < 3:
        #     job.status = "pending"
        #     job.retry_count += 1
        #     job.scheduled_at = datetime.utcnow() + timedelta(minutes=5 * job.retry_count)
        
    db.commit()
