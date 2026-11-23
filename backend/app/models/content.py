from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.models.enums import ContentAudience, ContentCategory, ContentStatus, db_enum

if TYPE_CHECKING:
    from app.models.user import User


class Article(TimestampMixin, Base):
    """Parenting guidance or child learning content. Health content needs reviewer approval."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    category: Mapped[ContentCategory] = mapped_column(db_enum(ContentCategory), index=True)
    audience: Mapped[ContentAudience] = mapped_column(
        db_enum(ContentAudience), default=ContentAudience.PARENT
    )
    min_age_months: Mapped[int | None] = mapped_column(Integer)
    max_age_months: Mapped[int | None] = mapped_column(Integer)
    cover_image_key: Mapped[str | None] = mapped_column(String(255))  # public bucket
    status: Mapped[ContentStatus] = mapped_column(
        db_enum(ContentStatus), default=ContentStatus.DRAFT, index=True
    )
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    author: Mapped["User | None"] = relationship(foreign_keys=[author_id])
    reviewed_by: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by_id])
