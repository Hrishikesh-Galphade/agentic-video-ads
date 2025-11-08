# services/asset-generator-agent/src/celery_app.py
from celery import Celery
from .core.config import settings

# Initialize the Celery application
celery = Celery(
    "asset_worker",
    broker=settings.CELERY_BROKER_URL,
    backend="rpc://", # Using RPC to send results back
    include=["src.tasks"] # Tell Celery where to find our tasks
)

celery.conf.update(
    task_track_started=True,
)