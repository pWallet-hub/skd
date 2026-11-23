from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, update

from app.api.deps import CurrentUser, DbSession
from app.models import Notification
from app.schemas.notification import NotificationRead

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    user: CurrentUser, db: DbSession, unread_only: bool = False
) -> list[Notification]:
    stmt = select(Notification).where(Notification.recipient_id == user.id)
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    return list(db.scalars(stmt.order_by(Notification.created_at.desc()).limit(100)))


@router.post("/{notification_id}/read", response_model=NotificationRead)
def mark_read(notification_id: int, user: CurrentUser, db: DbSession) -> Notification:
    n = db.get(Notification, notification_id)
    if n is None or n.recipient_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    n.read_at = n.read_at or datetime.now(UTC)
    db.commit()
    db.refresh(n)
    return n


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_read(user: CurrentUser, db: DbSession) -> None:
    db.execute(
        update(Notification)
        .where(Notification.recipient_id == user.id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(UTC))
    )
    db.commit()
