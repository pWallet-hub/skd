"""Community alert fan-out: turns an approved alert into individual notifications."""

from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, aliased

from app.models import AdministrativeArea, Child, CommunityAlert, Notification, User
from app.models.enums import AlertStatus, NotificationKind, UserRole


def recipient_ids(db: Session, alert: CommunityAlert) -> set[int]:
    """Parents with a child at a targeted school or living in a targeted area (or its children)."""
    area_ids = [a.id for a in alert.target_areas]
    school_ids = [s.id for s in alert.target_schools]
    if not area_ids and not school_ids:
        return set()

    child_area = aliased(AdministrativeArea)
    conditions = []
    if school_ids:
        conditions.append(Child.school_id.in_(school_ids))
    if area_ids:
        conditions.append(Child.area_id.in_(area_ids))
        conditions.append(child_area.parent_id.in_(area_ids))

    guardian_ids = set(
        db.scalars(
            select(Child.guardian_id)
            .outerjoin(child_area, child_area.id == Child.area_id)
            .where(or_(*conditions))
        )
    )
    if area_ids:
        guardian_ids |= set(
            db.scalars(
                select(User.id).where(User.role == UserRole.PARENT, User.home_area_id.in_(area_ids))
            )
        )
    return guardian_ids


def publish_alert(db: Session, alert: CommunityAlert) -> int:
    """Create one notification per recipient. Returns the number of notifications created."""
    if alert.status != AlertStatus.APPROVED:
        raise ValueError("Only approved alerts can be published")
    ids = recipient_ids(db, alert)
    db.add_all(
        Notification(
            recipient_id=uid,
            kind=NotificationKind.COMMUNITY_ALERT,
            title=alert.title,
            body=alert.message,
            alert_id=alert.id,
        )
        for uid in ids
    )
    alert.status = AlertStatus.PUBLISHED
    alert.published_at = datetime.now(UTC)
    db.commit()
    return len(ids)
