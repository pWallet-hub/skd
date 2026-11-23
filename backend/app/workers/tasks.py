import logging

from app.core.database import SessionLocal
from app.models import CommunityAlert
from app.services.alerts import publish_alert
from app.services.surveillance import detect_signals
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def detect_signals_task() -> dict[str, int]:
    with SessionLocal() as db:
        created, updated = detect_signals(db)
    logger.info("Signal detection finished: %s created, %s updated", created, updated)
    return {"created": created, "updated": updated}


@celery_app.task
def publish_alert_task(alert_id: int) -> int:
    with SessionLocal() as db:
        alert = db.get(CommunityAlert, alert_id)
        if alert is None:
            logger.warning("Alert %s no longer exists", alert_id)
            return 0
        sent = publish_alert(db, alert)
    logger.info("Alert %s published to %s recipients", alert_id, sent)
    return sent
