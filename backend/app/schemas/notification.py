from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import AlertSeverity, AlertStatus, NotificationKind
from app.schemas.common import ORMModel


class NotificationRead(ORMModel):
    id: int
    kind: NotificationKind
    title: str
    body: str
    alert_id: int | None
    read_at: datetime | None
    created_at: datetime


class AlertCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    message: str = Field(min_length=10)
    severity: AlertSeverity = AlertSeverity.ADVISORY
    signal_id: int | None = None
    target_area_ids: list[int] = Field(default_factory=list)
    target_school_ids: list[int] = Field(default_factory=list)


class AlertUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    message: str | None = Field(default=None, min_length=10)
    severity: AlertSeverity | None = None
    target_area_ids: list[int] | None = None
    target_school_ids: list[int] | None = None


class AlertRead(ORMModel):
    id: int
    title: str
    message: str
    severity: AlertSeverity
    status: AlertStatus
    signal_id: int | None
    created_by_id: int | None
    approved_by_id: int | None
    approved_at: datetime | None
    published_at: datetime | None
    target_area_ids: list[int]
    target_school_ids: list[int]
    created_at: datetime
