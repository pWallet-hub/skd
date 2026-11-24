"""Creating symptom reports and the notifications that follow them.

Shared by the API (parents) and the demo activity simulator so both behave identically.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Article, Child, Notification, Symptom, SymptomReport, User
from app.models.enums import ContentStatus, NotificationKind, ReportVerification, SymptomCategory

# Guidance shown after a report, by symptom category (most urgent first).
GUIDANCE = {
    SymptomCategory.RESPIRATORY: (
        "Watch the breathing",
        "Seek care immediately if breathing is fast, noisy or the chest pulls in. "
        "Keep your child hydrated and rested.",
        None,
    ),
    SymptomCategory.GASTROINTESTINAL: (
        "Keep your child hydrated",
        "Give small, frequent drinks (ORS if available) and continue feeding. "
        "Seek care if there is blood in the stool, repeated vomiting or signs of dehydration.",
        "when-to-seek-care-diarrhea",
    ),
    SymptomCategory.FEVER: (
        "Managing a fever",
        "Keep your child cool and give plenty of fluids. Seek care if the fever lasts more "
        "than 2 days, or comes with a stiff neck, rash or unusual drowsiness.",
        None,
    ),
    SymptomCategory.SKIN: (
        "About skin rashes",
        "Keep the skin clean and dry. Seek care if the rash spreads quickly or comes with fever.",
        None,
    ),
}


def create_report(
    db: Session,
    *,
    child: Child,
    reporter: User,
    symptoms: list[Symptom],
    onset_date: date,
    visited_facility: bool = False,
    facility_id: int | None = None,
    school_id: int | None = None,
    area_id: int | None = None,
    consent_to_aggregate: bool = True,
    notes: str | None = None,
    is_ongoing: bool = True,
    recovered_on: date | None = None,
) -> SymptomReport:
    """Create a report plus the parent's confirmation and guidance notifications. Caller commits."""
    report = SymptomReport(
        child_id=child.id,
        reported_by_id=reporter.id,
        symptoms=symptoms,
        onset_date=onset_date,
        visited_facility=visited_facility,
        facility_id=facility_id,
        school_id=school_id or child.school_id,
        area_id=area_id or child.area_id,
        consent_to_aggregate=consent_to_aggregate,
        notes=notes,
        is_ongoing=is_ongoing if recovered_on is None else False,
        recovered_on=recovered_on,
    )
    db.add(report)

    names = ", ".join(s.name.lower() for s in symptoms)
    db.add(
        Notification(
            recipient_id=reporter.id,
            kind=NotificationKind.FOLLOW_UP,
            title=f"Report received for {child.display_name}",
            body=f"Thank you. We recorded {names} starting {onset_date:%d %b}. "
            "You can update the report when your child recovers.",
        )
    )

    categories = {s.category for s in symptoms}
    for category, (title, body, slug) in GUIDANCE.items():
        if category not in categories:
            continue
        if slug and db.scalar(
            select(Article.id).where(
                Article.slug == slug, Article.status == ContentStatus.PUBLISHED
            )
        ):
            body += " Read more in Guidance."
        db.add(
            Notification(
                recipient_id=reporter.id, kind=NotificationKind.GUIDANCE, title=title, body=body
            )
        )
        break  # one guidance message per report is enough
    return report


def notify_verification(db: Session, report: SymptomReport) -> None:
    """Tell the parent when a health professional reviews their report. Caller commits."""
    if report.reported_by_id is None:
        return
    child_name = report.child.display_name if report.child else "your child"
    if report.verification == ReportVerification.CLINICALLY_CONFIRMED:
        body = (
            f"A health professional reviewed the report for {child_name} and confirmed it "
            "clinically. Please follow the advice of your health facility."
        )
    else:
        body = f"A health professional reviewed the report for {child_name}."
    db.add(
        Notification(
            recipient_id=report.reported_by_id,
            kind=NotificationKind.FOLLOW_UP,
            title="Your report was reviewed",
            body=body,
        )
    )
