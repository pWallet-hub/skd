"""Administration API: users, platform statistics, system health, audit log, settings."""

import secrets
import time
from datetime import UTC, date, datetime, timedelta

import redis
from fastapi import APIRouter, HTTPException, Query, Request, status
from sqlalchemy import Date, cast, func, or_, select, text

from app.api.deps import AdminUser, DbSession, get_or_404
from app.core.config import settings
from app.core.security import hash_password
from app.core.storage import bucket_for, internal_client
from app.core.version import VERSION
from app.models import (
    Article,
    AuditLog,
    Child,
    HealthFacility,
    InfrastructureAsset,
    School,
    SymptomReport,
    SystemSetting,
    User,
)
from app.models.enums import ContentStatus, UserRole
from app.schemas.admin import (
    AdminStats,
    AdminUserCreate,
    AdminUserRead,
    AdminUserUpdate,
    AuditLogRead,
    BucketUsage,
    DailyCount,
    DemoStatus,
    DemoToggle,
    Page,
    PasswordReset,
    RoleCount,
    ServiceStatus,
    SystemStatus,
    UserCreated,
)
from app.services import audit
from app.services.demo import LAST_RUN_KEY, simulate_activity
from app.services.system_settings import (
    DetectionSettings,
    defaults,
    get_detection_settings,
    is_demo_mode,
    save_detection_settings,
    set_demo_mode,
)

router = APIRouter(prefix="/admin", tags=["administration"])


def _temporary_password() -> str:
    return secrets.token_urlsafe(9)


def _user_read(db: DbSession, user: User) -> AdminUserRead:
    data = AdminUserRead.model_validate(user)
    data.children_count = (
        db.scalar(select(func.count(Child.id)).where(Child.guardian_id == user.id)) or 0
    )
    return data


# ------------------------------------------------------------------ users ----
@router.get("/users", response_model=Page[AdminUserRead])
def list_users(
    db: DbSession,
    _: AdminUser,
    search: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Page[AdminUserRead]:
    stmt = select(User)
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(or_(User.email.ilike(like), User.full_name.ilike(like)))
    if role:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active.is_(is_active))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    children = (
        select(Child.guardian_id, func.count(Child.id).label("n"))
        .group_by(Child.guardian_id)
        .subquery()
    )
    rows = db.execute(
        stmt.add_columns(func.coalesce(children.c.n, 0))
        .outerjoin(children, children.c.guardian_id == User.id)
        .order_by(User.created_at.desc(), User.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    items = []
    for user, n in rows:
        item = AdminUserRead.model_validate(user)
        item.children_count = n
        items.append(item)
    return Page[AdminUserRead](items=items, total=total)


@router.post("/users", response_model=UserCreated, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AdminUserCreate, admin: AdminUser, db: DbSession, request: Request
) -> UserCreated:
    email = payload.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    temporary = None if payload.password else _temporary_password()
    user = User(
        email=email,
        full_name=payload.full_name,
        role=payload.role,
        phone_number=payload.phone_number,
        home_area_id=payload.home_area_id,
        password_hash=hash_password(payload.password or temporary),
    )
    db.add(user)
    db.flush()
    audit.record(
        db, admin, "user.create", "user", user.id,
        f"Created {payload.role} account {email}", {"role": payload.role}, request,
    )  # fmt: skip
    db.commit()
    db.refresh(user)
    return UserCreated(user=_user_read(db, user), temporary_password=temporary)


@router.get("/users/{user_id}", response_model=AdminUserRead)
def get_user(user_id: int, db: DbSession, _: AdminUser) -> AdminUserRead:
    return _user_read(db, get_or_404(db, User, user_id))


@router.patch("/users/{user_id}", response_model=AdminUserRead)
def update_user(
    user_id: int, payload: AdminUserUpdate, admin: AdminUser, db: DbSession, request: Request
) -> AdminUserRead:
    user = get_or_404(db, User, user_id)
    data = payload.model_dump(exclude_unset=True)
    if user.id == admin.id and (
        data.get("is_active") is False or data.get("role", UserRole.ADMIN) != UserRole.ADMIN
    ):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "You cannot deactivate or demote your own account"
        )
    changes = {k: [str(getattr(user, k)), str(v)] for k, v in data.items() if getattr(user, k) != v}
    for field, value in data.items():
        setattr(user, field, value)
    if changes:
        action = "user.update"
        if "is_active" in changes:
            action = "user.activate" if user.is_active else "user.deactivate"
        elif "role" in changes:
            action = "user.role_change"
        audit.record(
            db, admin, action, "user", user.id,
            f"Updated {user.email}: {', '.join(changes)}", changes, request,
        )  # fmt: skip
    db.commit()
    db.refresh(user)
    return _user_read(db, user)


@router.post("/users/{user_id}/reset-password", response_model=PasswordReset)
def reset_password(
    user_id: int, admin: AdminUser, db: DbSession, request: Request
) -> PasswordReset:
    """Sets a new temporary password. Share it with the user through a secure channel."""
    user = get_or_404(db, User, user_id)
    temporary = _temporary_password()
    user.password_hash = hash_password(temporary)
    audit.record(
        db, admin, "user.password_reset", "user", user.id,
        f"Reset password for {user.email}", request=request,
    )  # fmt: skip
    db.commit()
    return PasswordReset(temporary_password=temporary)


# ------------------------------------------------------------------ stats ----
def _daily(db: DbSession, column, days: int, *where) -> list[DailyCount]:
    since = date.today() - timedelta(days=days - 1)
    day = cast(column, Date)
    counts = dict(
        db.execute(select(day, func.count()).where(day >= since, *where).group_by(day)).all()
    )
    return [
        DailyCount(day=since + timedelta(days=i), count=counts.get(since + timedelta(days=i), 0))
        for i in range(days)
    ]


@router.get("/stats", response_model=AdminStats)
def stats(db: DbSession, _: AdminUser) -> AdminStats:
    now = datetime.now(UTC)
    count = lambda stmt: db.scalar(stmt) or 0  # noqa: E731
    by_role = dict(db.execute(select(User.role, func.count()).group_by(User.role)).all())
    total = sum(by_role.values())
    active = count(select(func.count(User.id)).where(User.is_active.is_(True)))
    return AdminStats(
        total_users=total,
        active_users=active,
        inactive_users=total - active,
        new_users_30d=count(
            select(func.count(User.id)).where(User.created_at >= now - timedelta(days=30))
        ),
        logins_7d=count(
            select(func.count(User.id)).where(User.last_login_at >= now - timedelta(days=7))
        ),
        users_by_role=[RoleCount(role=r, count=by_role.get(r, 0)) for r in UserRole],
        reports_per_day=_daily(db, SymptomReport.onset_date, 30),
        signups_per_day=_daily(db, User.created_at, 30),
        articles_published=count(
            select(func.count(Article.id)).where(Article.status == ContentStatus.PUBLISHED)
        ),
        articles_draft=count(
            select(func.count(Article.id)).where(Article.status != ContentStatus.PUBLISHED)
        ),
        schools=count(select(func.count(School.id))),
        facilities=count(select(func.count(HealthFacility.id))),
        infrastructure=count(select(func.count(InfrastructureAsset.id))),
    )


# ----------------------------------------------------------------- system ----
def _timed(name: str, check) -> ServiceStatus:
    start = time.perf_counter()
    try:
        detail = check()
        return ServiceStatus(
            name=name, ok=True, latency_ms=round((time.perf_counter() - start) * 1000, 1),
            detail=detail,
        )  # fmt: skip
    except Exception as exc:  # noqa: BLE001 - surface any failure to the admin
        return ServiceStatus(name=name, ok=False, latency_ms=None, detail=str(exc)[:200])


@router.get("/system", response_model=SystemStatus)
def system_status(db: DbSession, _: AdminUser) -> SystemStatus:
    from app.workers.celery_app import celery_app

    def check_db() -> str:
        return f"PostGIS {db.execute(text('SELECT postgis_lib_version()')).scalar_one()}"

    def check_redis() -> str:
        client = redis.Redis.from_url(settings.redis_url, socket_timeout=2)
        client.ping()
        return f"Redis {client.info('server')['redis_version']}"

    def check_storage() -> str:
        internal_client().list_buckets()
        return "SeaweedFS S3 API reachable"

    def check_workers() -> str:
        replies = celery_app.control.ping(timeout=1.0) or []
        if not replies:
            raise RuntimeError("No Celery workers responded")
        return f"{len(replies)} worker(s) online"

    services = [
        _timed("Database", check_db),
        _timed("Redis", check_redis),
        _timed("Object storage", check_storage),
        _timed("Background workers", check_workers),
    ]

    storage: list[BucketUsage] = []
    for visibility in ("public", "private"):
        bucket = bucket_for(visibility)
        objects = size = 0
        try:
            paginator = internal_client().get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=bucket):
                for obj in page.get("Contents", []):
                    objects += 1
                    size += obj["Size"]
        except Exception:  # noqa: BLE001
            pass
        storage.append(BucketUsage(bucket=bucket, objects=objects, size_bytes=size))

    return SystemStatus(
        environment=settings.environment, version=VERSION, services=services, storage=storage
    )


# ------------------------------------------------------------------ audit ----
@router.get("/audit-logs", response_model=Page[AuditLogRead])
def audit_logs(
    db: DbSession,
    _: AdminUser,
    action: str | None = None,
    entity_type: str | None = None,
    actor: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Page[AuditLogRead]:
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action.startswith(action))
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if actor:
        stmt = stmt.where(AuditLog.actor_email.ilike(f"%{actor}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit).offset(offset)
    )
    return Page[AuditLogRead](items=[AuditLogRead.model_validate(r) for r in rows], total=total)


# --------------------------------------------------------------- settings ----
@router.get("/settings/detection", response_model=DetectionSettings)
def read_detection_settings(db: DbSession, _: AdminUser) -> DetectionSettings:
    return get_detection_settings(db)


@router.get("/settings/detection/defaults", response_model=DetectionSettings)
def read_detection_defaults(_: AdminUser) -> DetectionSettings:
    return defaults()


@router.put("/settings/detection", response_model=DetectionSettings)
def update_detection_settings(
    payload: DetectionSettings, admin: AdminUser, db: DbSession, request: Request
) -> DetectionSettings:
    changes = save_detection_settings(db, payload, admin)
    if changes:
        audit.record(
            db, admin, "settings.update", "settings", "detection",
            f"Changed detection settings: {', '.join(changes)}", changes, request,
        )  # fmt: skip
    db.commit()
    return get_detection_settings(db)


# ------------------------------------------------------------------- demo ----
@router.get("/demo", response_model=DemoStatus)
def demo_status(db: DbSession, _: AdminUser) -> DemoStatus:
    last = db.get(SystemSetting, LAST_RUN_KEY)
    return DemoStatus(
        enabled=is_demo_mode(db),
        interval_seconds=settings.demo_activity_interval_seconds,
        last_run_at=last.value.get("at") if last else None,
        last_run_stats=last.value.get("stats") if last else None,
    )


@router.put("/demo", response_model=DemoStatus)
def update_demo_mode(
    payload: DemoToggle, admin: AdminUser, db: DbSession, request: Request
) -> DemoStatus:
    set_demo_mode(db, payload.enabled, admin)
    audit.record(
        db, admin, "settings.demo_mode", "settings", "demo",
        f"Demo activity simulation {'enabled' if payload.enabled else 'disabled'}", request=request,
    )  # fmt: skip
    db.commit()
    return demo_status(db, admin)


@router.post("/demo/simulate", response_model=dict[str, int])
def simulate_now(admin: AdminUser, db: DbSession, request: Request) -> dict[str, int]:
    """Generate one round of demo activity immediately (works even if demo mode is off)."""
    stats = simulate_activity(db)
    audit.record(
        db, admin, "demo.simulate", "settings", "demo",
        "Generated demo activity: " + ", ".join(f"{v} {k}" for k, v in stats.items() if v),
        stats, request,
    )  # fmt: skip
    db.commit()
    return stats
