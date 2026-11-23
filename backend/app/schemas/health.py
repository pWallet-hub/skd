from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import ReportVerification, SymptomCategory
from app.schemas.common import ORMModel


class SymptomRead(ORMModel):
    id: int
    code: str
    name: str
    category: SymptomCategory


class ReportCreate(BaseModel):
    child_id: int
    symptom_ids: list[int] = Field(min_length=1)
    onset_date: date
    is_ongoing: bool = True
    recovered_on: date | None = None
    visited_facility: bool = False
    facility_id: int | None = None
    # Defaults to the child's school/area when omitted.
    school_id: int | None = None
    area_id: int | None = None
    consent_to_aggregate: bool = True
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def check_dates(self) -> "ReportCreate":
        if self.onset_date > date.today():
            raise ValueError("onset_date cannot be in the future")
        if self.recovered_on and self.recovered_on < self.onset_date:
            raise ValueError("recovered_on cannot be before onset_date")
        return self


class ReportUpdate(BaseModel):
    is_ongoing: bool | None = None
    recovered_on: date | None = None
    visited_facility: bool | None = None
    facility_id: int | None = None
    notes: str | None = Field(default=None, max_length=2000)


class ReportVerify(BaseModel):
    verification: ReportVerification


class ReportRead(ORMModel):
    id: int
    child_id: int
    symptoms: list[SymptomRead]
    onset_date: date
    is_ongoing: bool
    recovered_on: date | None
    visited_facility: bool
    facility_id: int | None
    school_id: int | None
    area_id: int | None
    verification: ReportVerification
    consent_to_aggregate: bool
    notes: str | None
    created_at: datetime
