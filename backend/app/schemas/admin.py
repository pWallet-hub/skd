from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole
from app.schemas.common import ORMModel


class Page[T](BaseModel):
    items: list[T]
    total: int


class AdminUserRead(ORMModel):
    id: int
    email: EmailStr
    full_name: str
    phone_number: str | None
    role: UserRole
    is_active: bool
    home_area_id: int | None
    last_login_at: datetime | None
    created_at: datetime
    children_count: int = 0


class AdminUserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)
    role: UserRole
    phone_number: str | None = Field(default=None, max_length=32)
    home_area_id: int | None = None
    # Leave empty to generate a temporary password.
    password: str | None = Field(default=None, min_length=8, max_length=128)


class AdminUserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    role: UserRole | None = None
    is_active: bool | None = None
    phone_number: str | None = Field(default=None, max_length=32)
    home_area_id: int | None = None


class UserCreated(BaseModel):
    user: AdminUserRead
    temporary_password: str | None


class PasswordReset(BaseModel):
    temporary_password: str


class RoleCount(BaseModel):
    role: UserRole
    count: int


class DailyCount(BaseModel):
    day: date
    count: int


class AdminStats(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    new_users_30d: int
    logins_7d: int
    users_by_role: list[RoleCount]
    reports_per_day: list[DailyCount]
    signups_per_day: list[DailyCount]
    articles_published: int
    articles_draft: int
    schools: int
    facilities: int
    infrastructure: int


class ServiceStatus(BaseModel):
    name: str
    ok: bool
    latency_ms: float | None
    detail: str


class BucketUsage(BaseModel):
    bucket: str
    objects: int
    size_bytes: int


class SystemStatus(BaseModel):
    environment: str
    version: str
    services: list[ServiceStatus]
    storage: list[BucketUsage]


class AuditLogRead(ORMModel):
    id: int
    actor_id: int | None
    actor_email: str | None
    action: str
    entity_type: str
    entity_id: str | None
    summary: str
    details: dict[str, Any]
    ip_address: str | None
    created_at: datetime


class DemoStatus(BaseModel):
    enabled: bool
    interval_seconds: int
    last_run_at: str | None
    last_run_stats: dict[str, int] | None


class DemoToggle(BaseModel):
    enabled: bool
