"""Per-child health tracking: immunizations and developmental milestones.

The schedules themselves (which vaccines, which milestones, at what age) live in code in
services/child_health.py; these tables only record what has actually happened for a child.
"""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.family import Child
    from app.models.geo import HealthFacility


class ImmunizationRecord(TimestampMixin, Base):
    __tablename__ = "immunization_records"
    __table_args__ = (UniqueConstraint("child_id", "vaccine_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="CASCADE"), index=True)
    vaccine_code: Mapped[str] = mapped_column(String(32))
    given_on: Mapped[date]
    facility_id: Mapped[int | None] = mapped_column(
        ForeignKey("health_facilities.id", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(Text)

    child: Mapped["Child"] = relationship(back_populates="immunizations")
    facility: Mapped["HealthFacility | None"] = relationship()


class MilestoneRecord(TimestampMixin, Base):
    __tablename__ = "milestone_records"
    __table_args__ = (UniqueConstraint("child_id", "milestone_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="CASCADE"), index=True)
    milestone_code: Mapped[str] = mapped_column(String(48))
    achieved_on: Mapped[date]

    child: Mapped["Child"] = relationship(back_populates="milestones")
