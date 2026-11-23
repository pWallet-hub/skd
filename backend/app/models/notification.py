from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.models.enums import AlertSeverity, AlertStatus, NotificationKind, db_enum
from app.models.geo import AdministrativeArea, School
from app.models.surveillance import HealthSignal

if TYPE_CHECKING:
    from app.models.user import User


alert_target_areas = Table(
    "alert_target_areas",
    Base.metadata,
    Column("alert_id", ForeignKey("community_alerts.id", ondelete="CASCADE"), primary_key=True),
    Column("area_id", ForeignKey("administrative_areas.id", ondelete="CASCADE"), primary_key=True),
)

alert_target_schools = Table(
    "alert_target_schools",
    Base.metadata,
    Column("alert_id", ForeignKey("community_alerts.id", ondelete="CASCADE"), primary_key=True),
    Column("school_id", ForeignKey("schools.id", ondelete="CASCADE"), primary_key=True),
)


class CommunityAlert(TimestampMixin, Base):
    """Group message. Must be approved by a second person before it is published."""

    __tablename__ = "community_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    severity: Mapped[AlertSeverity] = mapped_column(db_enum(AlertSeverity))
    status: Mapped[AlertStatus] = mapped_column(
        db_enum(AlertStatus), default=AlertStatus.DRAFT, index=True
    )
    signal_id: Mapped[int | None] = mapped_column(
        ForeignKey("health_signals.id", ondelete="SET NULL")
    )
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    signal: Mapped[HealthSignal | None] = relationship()
    created_by: Mapped["User | None"] = relationship(foreign_keys=[created_by_id])
    approved_by: Mapped["User | None"] = relationship(foreign_keys=[approved_by_id])
    target_areas: Mapped[list[AdministrativeArea]] = relationship(secondary=alert_target_areas)
    target_schools: Mapped[list[School]] = relationship(secondary=alert_target_schools)


class Notification(TimestampMixin, Base):
    """Message to a single user (in-app; email/SMS delivery can be layered on later)."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[NotificationKind] = mapped_column(db_enum(NotificationKind))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    alert_id: Mapped[int | None] = mapped_column(
        ForeignKey("community_alerts.id", ondelete="SET NULL")
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    recipient: Mapped["User"] = relationship()
    alert: Mapped[CommunityAlert | None] = relationship()
