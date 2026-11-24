from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery("smartkids", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "detect-community-signals-hourly": {
            "task": "app.workers.tasks.detect_signals_task",
            "schedule": crontab(minute=5),
        },
        # Runs always, but only acts when demo mode is on (admin Settings / DEMO_MODE).
        "simulate-demo-activity": {
            "task": "app.workers.tasks.simulate_demo_activity_task",
            "schedule": float(settings.demo_activity_interval_seconds),
        },
    },
)
celery_app.autodiscover_tasks(["app.workers"])

# `celery -A app.workers.celery_app` looks for an attribute named `app` or `celery`.
app = celery_app
