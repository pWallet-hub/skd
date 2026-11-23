from fastapi import APIRouter, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession, ParentUser, ReviewerUser, get_or_404
from app.api.routes.children import get_owned_child
from app.models import Symptom, SymptomReport
from app.models.enums import UserRole
from app.schemas.health import ReportCreate, ReportRead, ReportUpdate, ReportVerify, SymptomRead
from app.services import audit

router = APIRouter(tags=["health reports"])


@router.get("/symptoms", response_model=list[SymptomRead])
def list_symptoms(db: DbSession, _: CurrentUser) -> list[Symptom]:
    return list(db.scalars(select(Symptom).order_by(Symptom.category, Symptom.name)))


@router.get("/reports", response_model=list[ReportRead])
def list_reports(
    user: CurrentUser,
    db: DbSession,
    child_id: int | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
) -> list[SymptomReport]:
    """Parents see reports for their own children only. Reviewers/admins see all."""
    stmt = select(SymptomReport).options(selectinload(SymptomReport.symptoms))
    if user.role == UserRole.PARENT:
        stmt = stmt.where(SymptomReport.reported_by_id == user.id)
    elif user.role not in (UserRole.HEALTH_REVIEWER, UserRole.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Individual reports are not available")
    if child_id is not None:
        stmt = stmt.where(SymptomReport.child_id == child_id)
    stmt = stmt.order_by(SymptomReport.onset_date.desc(), SymptomReport.id.desc())
    return list(db.scalars(stmt.limit(limit).offset(offset)))


@router.post("/reports", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def create_report(payload: ReportCreate, user: ParentUser, db: DbSession) -> SymptomReport:
    child = get_owned_child(db, user, payload.child_id)
    symptoms = list(db.scalars(select(Symptom).where(Symptom.id.in_(payload.symptom_ids))))
    if len(symptoms) != len(set(payload.symptom_ids)):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown symptom id")

    data = payload.model_dump(exclude={"symptom_ids", "child_id"})
    data["school_id"] = payload.school_id or child.school_id
    data["area_id"] = payload.area_id or child.area_id
    report = SymptomReport(child_id=child.id, reported_by_id=user.id, symptoms=symptoms, **data)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def _get_report_for(db: DbSession, user, report_id: int) -> SymptomReport:
    report = get_or_404(db, SymptomReport, report_id)
    if user.role == UserRole.PARENT and report.reported_by_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "SymptomReport not found")
    return report


@router.get("/reports/{report_id}", response_model=ReportRead)
def get_report(report_id: int, user: CurrentUser, db: DbSession) -> SymptomReport:
    if user.role not in (UserRole.PARENT, UserRole.HEALTH_REVIEWER, UserRole.ADMIN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Individual reports are not available")
    return _get_report_for(db, user, report_id)


@router.patch("/reports/{report_id}", response_model=ReportRead)
def update_report(
    report_id: int, payload: ReportUpdate, user: ParentUser, db: DbSession
) -> SymptomReport:
    report = _get_report_for(db, user, report_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(report, field, value)
    if report.recovered_on:
        report.is_ongoing = False
    db.commit()
    db.refresh(report)
    return report


@router.post("/reports/{report_id}/verification", response_model=ReportRead)
def verify_report(
    report_id: int, payload: ReportVerify, user: ReviewerUser, db: DbSession, request: Request
) -> SymptomReport:
    """Health reviewers mark a report as clinically confirmed (or back to observation)."""
    report = get_or_404(db, SymptomReport, report_id)
    report.verification = payload.verification
    audit.record(
        db, user, "report.verification", "report", report.id,
        f"Report #{report.id} marked {payload.verification}", request=request,
    )  # fmt: skip
    db.commit()
    db.refresh(report)
    return report
