from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import SignalStatus, SymptomCategory
from app.schemas.common import ORMModel, PointField


class SignalPlace(ORMModel):
    id: int
    name: str
    location: PointField = None


class SignalAreaPlace(ORMModel):
    id: int
    name: str
    centroid: PointField = None


class InvestigationNoteRead(ORMModel):
    id: int
    author_id: int | None
    body: str
    status_change: str | None
    created_at: datetime


class SignalRead(ORMModel):
    id: int
    symptom_category: SymptomCategory
    area: SignalAreaPlace | None
    school: SignalPlace | None
    window_start: date
    window_end: date
    report_count: int
    baseline_count: float
    score: float
    status: SignalStatus
    assigned_to_id: int | None
    findings: str | None
    detected_at: datetime


class SignalDetail(SignalRead):
    notes: list[InvestigationNoteRead]


class SignalTransition(BaseModel):
    status: SignalStatus
    note: str = Field(min_length=3, max_length=4000)
    findings: str | None = None


class NoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class DetectionResult(BaseModel):
    created: int
    updated: int
