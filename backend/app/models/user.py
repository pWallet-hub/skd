from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.models.enums import UserRole, db_enum

if TYPE_CHECKING:
    from app.models.family import Child
    from app.models.geo import AdministrativeArea


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(150))
    phone_number: Mapped[str | None] = mapped_column(String(32))
    role: Mapped[UserRole] = mapped_column(db_enum(UserRole), default=UserRole.PARENT, index=True)
    preferred_language: Mapped[str] = mapped_column(String(8), default="en")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    home_area_id: Mapped[int | None] = mapped_column(
        ForeignKey("administrative_areas.id", ondelete="SET NULL")
    )

    home_area: Mapped["AdministrativeArea | None"] = relationship()
    children: Mapped[list["Child"]] = relationship(
        back_populates="guardian", cascade="all, delete-orphan"
    )
