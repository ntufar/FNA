"""
Celery application configuration for async task processing.

Provides Celery app instance configured with PostgreSQL broker and result backend.
"""

from celery import Celery
from celery.schedules import crontab

from .config import get_settings

settings = get_settings()

# PostgreSQL configuration for Celery broker and result backend
# Uses database URL from settings (same database as application)
database_url = settings.database_url

# Create Celery app with PostgreSQL as broker and backend
# Celery uses SQLAlchemy transport for database broker
celery_app = Celery(
    "fna_platform",
    broker=f"sqla+{database_url}",
    backend=f"db+{database_url}",
    include=["backend.src.tasks.batch_processing"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "backend.src.tasks.batch_processing.process_batch_reports": {"queue": "batch_processing"},
        "backend.src.tasks.batch_processing.process_single_report": {"queue": "report_processing"},
    },
    
    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minute soft limit
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    
    # Result backend
    result_expires=3600,  # Results expire after 1 hour
    
    # Beat schedule (for periodic tasks if needed)
    beat_schedule={
        # Example: Clean up old batch jobs daily
        # "cleanup-old-batch-jobs": {
        #     "task": "backend.src.tasks.batch_processing.cleanup_old_batch_jobs",
        #     "schedule": crontab(hour=2, minute=0),
        # },
    },
)

# Set default queue
celery_app.conf.task_default_queue = "default"

def get_celery_app() -> Celery:
    """Get configured Celery app instance."""
    return celery_app

