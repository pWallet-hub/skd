"""Aggregated, de-identified analytics. Nothing here returns data about an individual child."""

from collections import defaultdict
from datetime import date, timedelta

from geoalchemy2.shape import to_shape
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AdministrativeArea,
    Child,
    CommunityAlert,
    HealthSignal,
    School,
    Symptom,
    SymptomReport,
    User,
    report_symptoms,
)
from app.models.enums import AlertStatus, SymptomCategory, UserRole
from app.schemas.analytics import (
    AreaAggregate,
    CategoryCount,
    Overview,
    SchoolAggregate,
    TrendPoint,
)
from app.schemas.common import LatLng
from app.services.surveillance import OPEN_STATUSES
from app.services.system_settings import get_detection_settings


def _since(days: int) -> date:
    return date.today() - timedelta(days=days - 1)


def _suppress(count: int, min_size: int) -> tuple[int | None, bool]:
    if count < min_size:
        return None, True
    return count, False


def _latlng(geom) -> LatLng | None:
    if geom is None:
        return None
    p = to_shape(geom)
    return LatLng(latitude=p.y, longitude=p.x)


def _category_filter(stmt, category: SymptomCategory | None):
    if category is None:
        return stmt
    return (
        stmt.join(report_symptoms, report_symptoms.c.report_id == SymptomReport.id)
        .join(Symptom, Symptom.id == report_symptoms.c.symptom_id)
        .where(Symptom.category == category)
    )


def overview(db: Session) -> Overview:
    return Overview(
        families=db.scalar(select(func.count()).where(User.role == UserRole.PARENT)) or 0,
        children=db.scalar(select(func.count(Child.id))) or 0,
        reports_total=db.scalar(select(func.count(SymptomReport.id))) or 0,
        reports_last_7_days=db.scalar(
            select(func.count(SymptomReport.id)).where(SymptomReport.onset_date >= _since(7))
        )
        or 0,
        open_signals=db.scalar(
            select(func.count(HealthSignal.id)).where(HealthSignal.status.in_(OPEN_STATUSES))
        )
        or 0,
        published_alerts=db.scalar(
            select(func.count(CommunityAlert.id)).where(
                CommunityAlert.status == AlertStatus.PUBLISHED
            )
        )
        or 0,
    )


def area_aggregates(
    db: Session, days: int, category: SymptomCategory | None
) -> list[AreaAggregate]:
    min_size = get_detection_settings(db).aggregate_min_cell_size
    base = select(SymptomReport.area_id, func.count(func.distinct(SymptomReport.id))).where(
        SymptomReport.consent_to_aggregate.is_(True),
        SymptomReport.onset_date >= _since(days),
        SymptomReport.area_id.is_not(None),
    )
    counts = dict(
        db.execute(_category_filter(base, category).group_by(SymptomReport.area_id)).all()
    )

    top_stmt = (
        select(SymptomReport.area_id, Symptom.category, func.count())
        .join(report_symptoms, report_symptoms.c.report_id == SymptomReport.id)
        .join(Symptom, Symptom.id == report_symptoms.c.symptom_id)
        .where(
            SymptomReport.consent_to_aggregate.is_(True),
            SymptomReport.onset_date >= _since(days),
        )
        .group_by(SymptomReport.area_id, Symptom.category)
    )
    best: dict[int, tuple[SymptomCategory, int]] = {}
    for area_id, cat, n in db.execute(top_stmt):
        if area_id is not None and (area_id not in best or n > best[area_id][1]):
            best[area_id] = (SymptomCategory(cat), n)

    areas = db.scalars(select(AdministrativeArea).where(AdministrativeArea.id.in_(counts))).all()
    result = []
    for area in areas:
        count, suppressed = _suppress(counts[area.id], min_size)
        result.append(
            AreaAggregate(
                area_id=area.id,
                area_name=area.name,
                centroid=_latlng(area.centroid),
                report_count=count,
                suppressed=suppressed,
                top_category=None if suppressed else best.get(area.id, (None,))[0],
            )
        )
    return sorted(result, key=lambda a: a.report_count or 0, reverse=True)


def school_aggregates(
    db: Session, days: int, category: SymptomCategory | None
) -> list[SchoolAggregate]:
    min_size = get_detection_settings(db).aggregate_min_cell_size
    base = select(SymptomReport.school_id, func.count(func.distinct(SymptomReport.id))).where(
        SymptomReport.consent_to_aggregate.is_(True),
        SymptomReport.onset_date >= _since(days),
        SymptomReport.school_id.is_not(None),
    )
    counts = dict(
        db.execute(_category_filter(base, category).group_by(SymptomReport.school_id)).all()
    )
    schools = db.scalars(select(School).where(School.id.in_(counts))).all()
    result = []
    for s in schools:
        count, suppressed = _suppress(counts[s.id], min_size)
        result.append(
            SchoolAggregate(
                school_id=s.id,
                school_name=s.name,
                location=_latlng(s.location),
                report_count=count,
                suppressed=suppressed,
            )
        )
    return sorted(result, key=lambda a: a.report_count or 0, reverse=True)


def trends(db: Session, days: int) -> list[TrendPoint]:
    stmt = (
        select(
            SymptomReport.onset_date, Symptom.category, func.count(func.distinct(SymptomReport.id))
        )
        .join(report_symptoms, report_symptoms.c.report_id == SymptomReport.id)
        .join(Symptom, Symptom.id == report_symptoms.c.symptom_id)
        .where(
            SymptomReport.consent_to_aggregate.is_(True),
            SymptomReport.onset_date >= _since(days),
        )
        .group_by(SymptomReport.onset_date, Symptom.category)
        .order_by(SymptomReport.onset_date)
    )
    return [TrendPoint(day=d, category=SymptomCategory(c), count=n) for d, c, n in db.execute(stmt)]


def category_counts(db: Session, days: int) -> list[CategoryCount]:
    totals: dict[SymptomCategory, int] = defaultdict(int)
    for point in trends(db, days):
        totals[point.category] += point.count
    return sorted(
        (CategoryCount(category=c, count=n) for c, n in totals.items()),
        key=lambda c: c.count,
        reverse=True,
    )
