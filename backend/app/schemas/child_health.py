from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.services.child_health import MILESTONE_BY_CODE, VACCINE_BY_CODE


class ImmunizationItem(BaseModel):
    code: str
    name: str
    protects_against: str
    due_date: date
    status: str  # given | due | overdue | upcoming
    given_on: date | None
    record_id: int | None


class ImmunizationCreate(BaseModel):
    vaccine_code: str
    given_on: date
    facility_id: int | None = None
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("vaccine_code")
    @classmethod
    def known_vaccine(cls, v: str) -> str:
        if v not in VACCINE_BY_CODE:
            raise ValueError("Unknown vaccine code")
        return v

    @field_validator("given_on")
    @classmethod
    def not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Date cannot be in the future")
        return v


class MilestoneItem(BaseModel):
    code: str
    title: str
    domain: str
    expected_months: int
    status: str  # achieved | expected | check | upcoming
    achieved_on: date | None
    record_id: int | None


class MilestoneCreate(BaseModel):
    milestone_code: str
    achieved_on: date

    @field_validator("milestone_code")
    @classmethod
    def known_milestone(cls, v: str) -> str:
        if v not in MILESTONE_BY_CODE:
            raise ValueError("Unknown milestone code")
        return v

    @field_validator("achieved_on")
    @classmethod
    def not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Date cannot be in the future")
        return v


class CareSummary(BaseModel):
    vaccines_due: int
    vaccines_overdue: int
    milestones_to_check: int
