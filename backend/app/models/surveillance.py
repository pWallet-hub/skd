"""Community health signals: automatically detected unusual patterns that need HUMAN review."""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.models.enums import SignalStatus, SymptomCategory, db_enum
from app.models.geo import AdministrativeArea, School

if TYPE_CHECKING:
    from app.models.user import User


class HealthSignal(TimestampMixin, Base):
    """A *potential* cluster. Never proof of an outbreak or of its cause."""

    __tablename__ = "health_signals"

    id: Mapped[int] = mapped_column(primary_key=True)
    symptom_category: Mapped[SymptomCategory] = mapped_column(db_enum(SymptomCategory), index=True)
    # Exactly one of area/school is set: the grouping the pattern was detected in.
    area_id: Mapped[int | None] = mapped_column(
        ForeignKey("administrative_areas.id", ondelete="CASCADE")
    )
    school_id: Mapped[int | None] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"))
    window_start: Mapped[date] = mapped_column(Date)
    window_end: Mapped[date] = mapped_column(Date)
    report_count: Mapped[int] = mapped_column(Integer)
    baseline_count: Mapped[float] = mapped_column(Float)
    score: Mapped[float] = mapped_column(Float)
    status: Mapped[SignalStatus] = mapped_column(
        db_enum(SignalStatus), default=SignalStatus.DETECTED, index=True
    )
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    findings: Mapped[str | None] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    area: Mapped[AdministrativeArea | None] = relationship()
    school: Mapped[School | None] = relationship()
    assigned_to: Mapped["User | None"] = relationship()
    notes: Mapped[list["InvestigationNote"]] = relationship(
        back_populates="signal",
        cascade="all, delete-orphan",
        order_by="InvestigationNote.created_at",
    )


class InvestigationNote(TimestampMixin, Base):
    """Audit trail of the human review of a signal."""

    __tablename__ = "investigation_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    signal_id: Mapped[int] = mapped_column(
        ForeignKey("health_signals.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    body: Mapped[str] = mapped_column(Text)
    status_change: Mapped[str | None] = mapped_column(String(64))

    signal: Mapped[HealthSignal] = relationship(back_populates="notes")
    author: Mapped["User | None"] = relationship()
