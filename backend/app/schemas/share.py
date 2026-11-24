from datetime import date, datetime

from pydantic import BaseModel, Field


class ShareRequest(BaseModel):
    hours: int = Field(default=24, ge=1, le=168)


class ShareLink(BaseModel):
    token: str
    url: str
    expires_at: datetime


class HealthCardVaccine(BaseModel):
    name: str
    status: str
    given_on: date | None
    due_date: date


class HealthCard(BaseModel):
    """What a health worker sees after scanning the QR code. Read-only, minimal."""

    display_name: str
    age_months: int
    date_of_birth: date
    sex: str
    latest_height_cm: float | None
    latest_weight_kg: float | None
    measured_on: date | None
    vaccines: list[HealthCardVaccine]
    recent_concerns: list[str]
    health_notes: str | None
    expires_at: datetime
