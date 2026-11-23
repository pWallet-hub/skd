from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, HealthTeamUser, InsightUser, ReviewerUser, get_or_404
from app.models import AdministrativeArea, CommunityAlert, School
from app.models.enums import AlertStatus
from app.schemas.notification import AlertCreate, AlertRead, AlertUpdate
from app.workers.tasks import publish_alert_task

router = APIRouter(prefix="/alerts", tags=["community alerts"])


def to_read(alert: CommunityAlert) -> AlertRead:
    return AlertRead.model_validate(
        {
            **{f: getattr(alert, f) for f in AlertRead.model_fields if hasattr(alert, f)},
            "target_area_ids": [a.id for a in alert.target_areas],
            "target_school_ids": [s.id for s in alert.target_schools],
        }
    )


def _set_targets(db: DbSession, alert: CommunityAlert, area_ids, school_ids) -> None:
    if area_ids is not None:
        alert.target_areas = list(
            db.scalars(select(AdministrativeArea).where(AdministrativeArea.id.in_(area_ids)))
        )
    if school_ids is not None:
        alert.target_schools = list(db.scalars(select(School).where(School.id.in_(school_ids))))


def _require_status(alert: CommunityAlert, *allowed: AlertStatus) -> None:
    if alert.status not in allowed:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Not allowed while alert is '{alert.status}'"
        )


@router.get("", response_model=list[AlertRead])
def list_alerts(db: DbSession, _: InsightUser) -> list[AlertRead]:
    alerts = db.scalars(select(CommunityAlert).order_by(CommunityAlert.created_at.desc()))
    return [to_read(a) for a in alerts]


@router.post("", response_model=AlertRead, status_code=status.HTTP_201_CREATED)
def create_alert(payload: AlertCreate, user: HealthTeamUser, db: DbSession) -> AlertRead:
    alert = CommunityAlert(
        **payload.model_dump(exclude={"target_area_ids", "target_school_ids"}),
        created_by_id=user.id,
    )
    _set_targets(db, alert, payload.target_area_ids, payload.target_school_ids)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return to_read(alert)


@router.get("/{alert_id}", response_model=AlertRead)
def get_alert(alert_id: int, db: DbSession, _: InsightUser) -> AlertRead:
    return to_read(get_or_404(db, CommunityAlert, alert_id))


@router.patch("/{alert_id}", response_model=AlertRead)
def update_alert(
    alert_id: int, payload: AlertUpdate, _: HealthTeamUser, db: DbSession
) -> AlertRead:
    alert = get_or_404(db, CommunityAlert, alert_id)
    _require_status(alert, AlertStatus.DRAFT)
    data = payload.model_dump(exclude_unset=True)
    _set_targets(db, alert, data.pop("target_area_ids", None), data.pop("target_school_ids", None))
    for field, value in data.items():
        setattr(alert, field, value)
    db.commit()
    db.refresh(alert)
    return to_read(alert)


@router.post("/{alert_id}/submit", response_model=AlertRead)
def submit_alert(alert_id: int, _: HealthTeamUser, db: DbSession) -> AlertRead:
    alert = get_or_404(db, CommunityAlert, alert_id)
    _require_status(alert, AlertStatus.DRAFT)
    if not alert.target_areas and not alert.target_schools:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Alert has no target audience")
    alert.status = AlertStatus.PENDING_APPROVAL
    db.commit()
    return to_read(alert)


@router.post("/{alert_id}/approve", response_model=AlertRead)
def approve_alert(alert_id: int, user: ReviewerUser, db: DbSession) -> AlertRead:
    """Four-eyes rule: the approver must be a health reviewer and not the author."""
    alert = get_or_404(db, CommunityAlert, alert_id)
    _require_status(alert, AlertStatus.PENDING_APPROVAL)
    if alert.created_by_id == user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "An alert cannot be approved by its author")
    alert.status = AlertStatus.APPROVED
    alert.approved_by_id = user.id
    alert.approved_at = datetime.now(UTC)
    db.commit()
    return to_read(alert)


@router.post("/{alert_id}/reject", response_model=AlertRead)
def reject_alert(alert_id: int, _: ReviewerUser, db: DbSession) -> AlertRead:
    alert = get_or_404(db, CommunityAlert, alert_id)
    _require_status(alert, AlertStatus.PENDING_APPROVAL)
    alert.status = AlertStatus.DRAFT
    db.commit()
    return to_read(alert)


@router.post("/{alert_id}/publish", response_model=AlertRead, status_code=status.HTTP_202_ACCEPTED)
def publish_alert(alert_id: int, _: HealthTeamUser, db: DbSession) -> AlertRead:
    """Queues delivery to all targeted families (Celery worker)."""
    alert = get_or_404(db, CommunityAlert, alert_id)
    _require_status(alert, AlertStatus.APPROVED)
    publish_alert_task.delay(alert.id)
    return to_read(alert)


@router.post("/{alert_id}/retract", response_model=AlertRead)
def retract_alert(alert_id: int, _: ReviewerUser, db: DbSession) -> AlertRead:
    alert = get_or_404(db, CommunityAlert, alert_id)
    _require_status(alert, AlertStatus.PUBLISHED, AlertStatus.APPROVED)
    alert.status = AlertStatus.RETRACTED
    db.commit()
    return to_read(alert)
