from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import Sex
from app.schemas.common import ORMModel


class ChildBase(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    sex: Sex = Sex.UNSPECIFIED
    school_id: int | None = None
    area_id: int | None = None
    learning_interests: list[str] = Field(default_factory=list)
    health_notes: str | None = None


class ChildCreate(ChildBase):
    pass


class ChildUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    date_of_birth: date | None = None
    sex: Sex | None = None
    school_id: int | None = None
    area_id: int | None = None
    learning_interests: list[str] | None = None
    health_notes: str | None = None


class ChildRead(ChildBase, ORMModel):
    id: int
    guardian_id: int
    photo_url: str | None = None
    age_months: int


class MeasurementCreate(BaseModel):
    measured_on: date
    height_cm: Decimal | None = Field(default=None, gt=0, lt=250)
    weight_kg: Decimal | None = Field(default=None, gt=0, lt=250)
    head_circumference_cm: Decimal | None = Field(default=None, gt=0, lt=100)
    notes: str | None = None


class MeasurementRead(MeasurementCreate, ORMModel):
    id: int
    child_id: int
