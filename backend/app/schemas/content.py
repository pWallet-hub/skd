from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ContentAudience, ContentCategory, ContentStatus
from app.schemas.common import ORMModel


class ArticleCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=160)
    title: str = Field(min_length=3, max_length=200)
    summary: str = Field(max_length=500)
    body: str
    category: ContentCategory
    audience: ContentAudience = ContentAudience.PARENT
    min_age_months: int | None = Field(default=None, ge=0)
    max_age_months: int | None = Field(default=None, ge=0)


class ArticleUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    body: str | None = None
    category: ContentCategory | None = None
    audience: ContentAudience | None = None
    min_age_months: int | None = None
    max_age_months: int | None = None
    status: ContentStatus | None = None


class ArticleRead(ORMModel):
    id: int
    slug: str
    title: str
    summary: str
    body: str
    category: ContentCategory
    audience: ContentAudience
    min_age_months: int | None
    max_age_months: int | None
    cover_image_url: str | None = None
    status: ContentStatus
    published_at: datetime | None
