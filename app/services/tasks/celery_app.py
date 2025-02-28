import logging
from celery import Celery

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery = Celery(
    "product_manager_enhancer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.services.tasks.analysis",
        "app.services.tasks.enhancements"
    ]
)

# Configure Celery
celery.conf.update(
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
    celery.conf.update(
        task_always_eager=True,  # Tasks run synchronously in development
        task_eager_propagates=True
    ) 