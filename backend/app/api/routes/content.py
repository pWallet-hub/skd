from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, UploadFile, status
from sqlalchemy import or_, select

from app.api.deps import AdminUser, CurrentUser, DbSession, HealthTeamUser, get_or_404
from app.core.storage import ALLOWED_IMAGE_TYPES, delete_file, file_url, upload_file
from app.models import Article
from app.models.enums import ContentAudience, ContentCategory, ContentStatus, UserRole
from app.schemas.content import ArticleCreate, ArticleRead, ArticleUpdate
from app.services import audit

router = APIRouter(prefix="/content/articles", tags=["content"])

EDITOR_ROLES = (UserRole.HEALTH_REVIEWER, UserRole.ANALYST, UserRole.ADMIN)


def to_read(a: Article) -> ArticleRead:
    return ArticleRead.model_validate(
        {
            **{f: getattr(a, f) for f in ArticleRead.model_fields if hasattr(a, f)},
            "cover_image_url": file_url(a.cover_image_key, "public"),
        }
    )


@router.get("", response_model=list[ArticleRead])
def list_articles(
    user: CurrentUser,
    db: DbSession,
    category: ContentCategory | None = None,
    audience: ContentAudience | None = None,
    age_months: int | None = None,
) -> list[ArticleRead]:
    stmt = select(Article).order_by(Article.published_at.desc().nulls_last(), Article.id.desc())
    if user.role not in EDITOR_ROLES:
        stmt = stmt.where(Article.status == ContentStatus.PUBLISHED)
    if category:
        stmt = stmt.where(Article.category == category)
    if audience:
        stmt = stmt.where(Article.audience == audience)
    if age_months is not None:
        stmt = stmt.where(
            or_(Article.min_age_months.is_(None), Article.min_age_months <= age_months),
            or_(Article.max_age_months.is_(None), Article.max_age_months >= age_months),
        )
    return [to_read(a) for a in db.scalars(stmt)]


@router.get("/{slug}", response_model=ArticleRead)
def get_article(slug: str, user: CurrentUser, db: DbSession) -> ArticleRead:
    article = db.scalar(select(Article).where(Article.slug == slug))
    if article is None or (
        article.status != ContentStatus.PUBLISHED and user.role not in EDITOR_ROLES
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Article not found")
    return to_read(article)


@router.post("", response_model=ArticleRead, status_code=status.HTTP_201_CREATED)
def create_article(payload: ArticleCreate, user: HealthTeamUser, db: DbSession) -> ArticleRead:
    if db.scalar(select(Article.id).where(Article.slug == payload.slug)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Slug already in use")
    article = Article(**payload.model_dump(), author_id=user.id)
    db.add(article)
    db.commit()
    db.refresh(article)
    return to_read(article)


@router.patch("/{article_id}", response_model=ArticleRead)
def update_article(
    article_id: int, payload: ArticleUpdate, user: HealthTeamUser, db: DbSession, request: Request
) -> ArticleRead:
    article = get_or_404(db, Article, article_id)
    data = payload.model_dump(exclude_unset=True)
    new_status = data.get("status")
    if new_status == ContentStatus.PUBLISHED and article.status != ContentStatus.PUBLISHED:
        # Health content must be published by a health reviewer.
        if article.category == ContentCategory.HEALTH and user.role not in (
            UserRole.HEALTH_REVIEWER,
            UserRole.ADMIN,
        ):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Health content must be approved by a health reviewer"
            )
        article.reviewed_by_id = user.id
        article.published_at = datetime.now(UTC)
    if new_status and new_status != article.status:
        audit.record(
            db, user, f"article.{new_status}", "article", article.id,
            f"Article '{article.title}' set to {new_status}", request=request,
        )  # fmt: skip
    for field, value in data.items():
        setattr(article, field, value)
    db.commit()
    db.refresh(article)
    return to_read(article)


@router.put("/{article_id}/cover", response_model=ArticleRead)
def upload_cover(
    article_id: int, file: UploadFile, _: HealthTeamUser, db: DbSession
) -> ArticleRead:
    """Stored in the PUBLIC SeaweedFS bucket."""
    article = get_or_404(db, Article, article_id)
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Unsupported image type")
    article.cover_image_key = upload_file(
        file.file,
        filename=file.filename or "cover",
        content_type=file.content_type,
        visibility="public",
        prefix="articles",
    )
    db.commit()
    return to_read(article)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(article_id: int, admin: AdminUser, db: DbSession, request: Request) -> None:
    article = get_or_404(db, Article, article_id)
    if article.cover_image_key:
        delete_file(article.cover_image_key, "public")
    audit.record(
        db, admin, "article.delete", "article", article.id,
        f"Deleted article '{article.title}'", request=request,
    )  # fmt: skip
    db.delete(article)
    db.commit()
