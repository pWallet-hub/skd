from fastapi import APIRouter, Query

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
