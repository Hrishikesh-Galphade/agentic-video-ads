# services/orchestrator-agent/src/workflow/celery_client.py
from celery import Celery
from ..core.config import settings

# This Celery app instance is ONLY for sending tasks, not for being a worker.
celery_app = Celery(
    "orchestrator_client",
    broker=settings.CELERY_BROKER_URL,
    backend="rpc://" # Must have a backend to get results
)