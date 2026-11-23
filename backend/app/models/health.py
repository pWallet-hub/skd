from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Date, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.models.enums import ReportVerification, SymptomCategory, db_enum
from app.models.geo import AdministrativeArea, HealthFacility, School

if TYPE_CHECKING:
    from app.models.family import Child
    from app.models.user import User


report_symptoms = Table(
    "report_symptoms",
    Base.metadata,
    Column("report_id", ForeignKey("symptom_reports.id", ondelete="CASCADE"), primary_key=True),
    Column("symptom_id", ForeignKey("symptoms.id", ondelete="RESTRICT"), primary_key=True),
)


class Symptom(Base):
    """Controlled vocabulary of symptoms a parent can report."""

    __tablename__ = "symptoms"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(48), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[SymptomCategory] = mapped_column(db_enum(SymptomCategory), index=True)


class SymptomReport(TimestampMixin, Base):
    """A parent's observation about a child's health. Not a diagnosis."""

    __tablename__ = "symptom_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="CASCADE"), index=True)
    reported_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    onset_date: Mapped[date] = mapped_column(Date, index=True)
    is_ongoing: Mapped[bool] = mapped_column(Boolean, default=True)
    recovered_on: Mapped[date | None]
    visited_facility: Mapped[bool] = mapped_column(Boolean, default=False)
    facility_id: Mapped[int | None] = mapped_column(
        ForeignKey("health_facilities.id", ondelete="SET NULL")
    )
    # Location context is copied at report time so later profile changes don't rewrite history.
    school_id: Mapped[int | None] = mapped_column(
        ForeignKey("schools.id", ondelete="SET NULL"), index=True
    )
    area_id: Mapped[int | None] = mapped_column(
        ForeignKey("administrative_areas.id", ondelete="SET NULL"), index=True
    )
    verification: Mapped[ReportVerification] = mapped_column(
        db_enum(ReportVerification), default=ReportVerification.PARENT_OBSERVATION
    )
    consent_to_aggregate: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)

    child: Mapped["Child"] = relationship()
    reported_by: Mapped["User | None"] = relationship()
    symptoms: Mapped[list[Symptom]] = relationship(secondary=report_symptoms)
    facility: Mapped[HealthFacility | None] = relationship()
    school: Mapped[School | None] = relationship()
    area: Mapped[AdministrativeArea | None] = relationship()
