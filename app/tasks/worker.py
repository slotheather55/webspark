import os
import logging
from celery import Celery

from app.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Celery app
celery_app = Celery(
    "product_enhancer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.services.tasks.analysis",
        "app.services.tasks.enhancements"
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    worker_max_tasks_per_child=100,
    worker_prefetch_multiplier=1  # One task per worker process
)

# Optional configuration for development
if settings.ENVIRONMENT == "development":
    celery_app.conf.update(
        task_always_eager=True,  # Tasks run synchronously in development
        task_eager_propagates=True
    )

if __name__ == "__main__":
    celery_app.start() 