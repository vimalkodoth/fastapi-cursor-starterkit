"""
Celery worker configuration.
"""
import os

from celery import Celery

app = Celery(
    "celery_api",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=["app.tasks.data"],
)
