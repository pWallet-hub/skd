import csv
import io
from datetime import date

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.api.deps import DbSession, InsightUser
from app.models.enums import SymptomCategory
from app.schemas.analytics import (
    AreaAggregate,
    CategoryCount,
    Overview,
    SchoolAggregate,
    TrendPoint,
)
from app.services import analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])

Days = Query(30, ge=1, le=365)


@router.get("/overview", response_model=Overview)
def overview(db: DbSession, _: InsightUser) -> Overview:
    return analytics.overview(db)


@router.get("/areas", response_model=list[AreaAggregate])
def by_area(
    db: DbSession, _: InsightUser, days: int = Days, category: SymptomCategory | None = None
) -> list[AreaAggregate]:
    return analytics.area_aggregates(db, days, category)


@router.get("/schools", response_model=list[SchoolAggregate])
def by_school(
    db: DbSession, _: InsightUser, days: int = Days, category: SymptomCategory | None = None
) -> list[SchoolAggregate]:
    return analytics.school_aggregates(db, days, category)


@router.get("/trends", response_model=list[TrendPoint])
def trends(db: DbSession, _: InsightUser, days: int = Days) -> list[TrendPoint]:
    return analytics.trends(db, days)


@router.get("/categories", response_model=list[CategoryCount])
def categories(db: DbSession, _: InsightUser, days: int = Days) -> list[CategoryCount]:
    return analytics.category_counts(db, days)


@router.get("/export.csv", response_class=StreamingResponse)
def export_csv(db: DbSession, _: InsightUser, days: int = Days) -> StreamingResponse:
    """De-identified aggregates (per area and per school), small counts suppressed."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["level", "id", "name", "report_count", "suppressed", "top_category"])
    for a in analytics.area_aggregates(db, days, None):
        writer.writerow(["area", a.area_id, a.area_name, a.report_count or "", a.suppressed,
                         a.top_category or ""])  # fmt: skip
    for s in analytics.school_aggregates(db, days, None):
        writer.writerow(["school", s.school_id, s.school_name, s.report_count or "", s.suppressed,
                         ""])  # fmt: skip
    filename = f"smartkids-aggregates-{date.today()}-{days}d.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
