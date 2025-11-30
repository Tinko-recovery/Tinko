import time
import logging
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from app.services.task_queue import run_pending_jobs
from app.db import Base, engine

# Ensure models are loaded
from app import models 
# Ensure tasks are registered by importing modules
from app.services import email_service
from app.services import sms_service
from app.tasks import retry_tasks

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def start_worker():
    logger.info("Starting Tinko Background Worker...")
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    while True:
        try:
            # Run up to 10 jobs at a time
            count = run_pending_jobs(limit=10)
            if count == 0:
                time.sleep(2) # Sleep if no jobs
        except KeyboardInterrupt:
            logger.info("Worker stopping...")
            break
        except Exception as e:
            logger.error(f"Worker crashed: {e}")
            time.sleep(5)

if __name__ == "__main__":
    start_worker()
