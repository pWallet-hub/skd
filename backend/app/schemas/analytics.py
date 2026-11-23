from datetime import date

from pydantic import BaseModel

from app.models.enums import SymptomCategory
from app.schemas.common import LatLng


class Overview(BaseModel):
    families: int
    children: int
    reports_total: int
    reports_last_7_days: int
    open_signals: int
    published_alerts: int


class AreaAggregate(BaseModel):
    """Aggregated, de-identified counts. Cells below the minimum size are suppressed."""

    area_id: int
    area_name: str
    centroid: LatLng | None
    report_count: int | None  # None = suppressed for privacy
    suppressed: bool
    top_category: SymptomCategory | None


class SchoolAggregate(BaseModel):
    school_id: int
    school_name: str
    location: LatLng | None
    report_count: int | None
    suppressed: bool


class TrendPoint(BaseModel):
    day: date
    category: SymptomCategory
    count: int


class CategoryCount(BaseModel):
    category: SymptomCategory
    count: int
