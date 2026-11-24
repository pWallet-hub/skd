from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.models.enums import Sex, db_enum
from app.models.geo import AdministrativeArea, School

if TYPE_CHECKING:
    from app.models.child_health import ImmunizationRecord, MilestoneRecord
    from app.models.user import User


class Child(TimestampMixin, Base):
    __tablename__ = "children"

    id: Mapped[int] = mapped_column(primary_key=True)
    guardian_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    date_of_birth: Mapped[date]
    sex: Mapped[Sex] = mapped_column(db_enum(Sex), default=Sex.UNSPECIFIED)
    school_id: Mapped[int | None] = mapped_column(ForeignKey("schools.id", ondelete="SET NULL"))
    area_id: Mapped[int | None] = mapped_column(
        ForeignKey("administrative_areas.id", ondelete="SET NULL")
    )
    photo_key: Mapped[str | None] = mapped_column(String(255))  # private bucket
    learning_interests: Mapped[list[str]] = mapped_column(JSON, default=list)
    health_notes: Mapped[str | None] = mapped_column(Text)

    guardian: Mapped["User"] = relationship(back_populates="children")
    school: Mapped[School | None] = relationship()
    area: Mapped[AdministrativeArea | None] = relationship()
    measurements: Mapped[list["GrowthMeasurement"]] = relationship(
        back_populates="child",
        cascade="all, delete-orphan",
        order_by="GrowthMeasurement.measured_on",
    )
    immunizations: Mapped[list["ImmunizationRecord"]] = relationship(
        back_populates="child", cascade="all, delete-orphan"
    )
    milestones: Mapped[list["MilestoneRecord"]] = relationship(
        back_populates="child", cascade="all, delete-orphan"
    )


class GrowthMeasurement(TimestampMixin, Base):
    __tablename__ = "growth_measurements"

    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="CASCADE"), index=True)
    measured_on: Mapped[date]
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    head_circumference_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    notes: Mapped[str | None] = mapped_column(Text)

    child: Mapped[Child] = relationship(back_populates="measurements")
