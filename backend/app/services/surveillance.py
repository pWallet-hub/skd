"""Community health signal detection.

Method (deliberately simple and explainable for the prototype). Thresholds come from
environment defaults, overridable by admins (see services/system_settings.py):

For every (school, symptom category) and (area, symptom category) pair we compare
  * the number of reports in the last SIGNAL_WINDOW_DAYS ("window"), with
  * the expected number, derived from the previous SIGNAL_BASELINE_DAYS ("baseline").

A signal is raised when
  window_count >= SIGNAL_MIN_REPORTS  and  window_count / max(expected, 1) >= SIGNAL_RATIO_THRESHOLD

Only reports with consent_to_aggregate = true are used. A signal is a prompt for HUMAN
review; it is never treated as a confirmed outbreak or as evidence of a cause.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.models import HealthSignal, Symptom, SymptomReport, report_symptoms
from app.models.enums import SignalStatus, SymptomCategory
from app.services.system_settings import get_detection_settings

OPEN_STATUSES = (SignalStatus.DETECTED, SignalStatus.UNDER_REVIEW, SignalStatus.CONFIRMED)

# Allowed review workflow transitions
TRANSITIONS: dict[SignalStatus, set[SignalStatus]] = {
    SignalStatus.DETECTED: {SignalStatus.UNDER_REVIEW, SignalStatus.DISMISSED},
    SignalStatus.UNDER_REVIEW: {SignalStatus.CONFIRMED, SignalStatus.DISMISSED},
    SignalStatus.CONFIRMED: {SignalStatus.RESOLVED},
    SignalStatus.DISMISSED: {SignalStatus.UNDER_REVIEW},
    SignalStatus.RESOLVED: set(),
}


@dataclass(frozen=True)
class Candidate:
    category: SymptomCategory
    school_id: int | None
    area_id: int | None
    window_count: int
    baseline_count: int
    expected: float
    score: float


def find_candidates(db: Session, today: date | None = None) -> tuple[date, date, list[Candidate]]:
    cfg = get_detection_settings(db)
    today = today or date.today()
    window_start = today - timedelta(days=cfg.signal_window_days - 1)
    baseline_start = window_start - timedelta(days=cfg.signal_baseline_days)
    scale = cfg.signal_window_days / cfg.signal_baseline_days

    in_window = SymptomReport.onset_date >= window_start
    in_baseline = and_(
        SymptomReport.onset_date >= baseline_start, SymptomReport.onset_date < window_start
    )

    candidates: list[Candidate] = []
    for group_col, is_school in ((SymptomReport.school_id, True), (SymptomReport.area_id, False)):
        stmt = (
            select(
                group_col,
                Symptom.category,
                func.count(func.distinct(case((in_window, SymptomReport.id)))),
                func.count(func.distinct(case((in_baseline, SymptomReport.id)))),
            )
            .join(report_symptoms, report_symptoms.c.report_id == SymptomReport.id)
            .join(Symptom, Symptom.id == report_symptoms.c.symptom_id)
            .where(
                SymptomReport.consent_to_aggregate.is_(True),
                SymptomReport.onset_date >= baseline_start,
                SymptomReport.onset_date <= today,
                group_col.is_not(None),
            )
            .group_by(group_col, Symptom.category)
        )
        for group_id, category, window_count, baseline_count in db.execute(stmt):
            expected = baseline_count * scale
            score = window_count / max(expected, 1.0)
            if window_count >= cfg.signal_min_reports and score >= cfg.signal_ratio_threshold:
                candidates.append(
                    Candidate(
                        category=SymptomCategory(category),
                        school_id=group_id if is_school else None,
                        area_id=None if is_school else group_id,
                        window_count=window_count,
                        baseline_count=baseline_count,
                        expected=round(expected, 2),
                        score=round(score, 2),
                    )
                )
    return window_start, today, candidates


def detect_signals(db: Session, today: date | None = None) -> tuple[int, int]:
    """Create or refresh open signals. Returns (created, updated)."""
    window_start, window_end, candidates = find_candidates(db, today)
    created = updated = 0
    for c in candidates:
        existing = db.scalar(
            select(HealthSignal).where(
                HealthSignal.symptom_category == c.category,
                HealthSignal.school_id.is_(None)
                if c.school_id is None
                else HealthSignal.school_id == c.school_id,
                HealthSignal.area_id.is_(None)
                if c.area_id is None
                else HealthSignal.area_id == c.area_id,
                HealthSignal.status.in_(OPEN_STATUSES),
            )
        )
        if existing:
            existing.window_end = window_end
            existing.report_count = c.window_count
            existing.baseline_count = c.expected
            existing.score = c.score
            updated += 1
        else:
            db.add(
                HealthSignal(
                    symptom_category=c.category,
                    school_id=c.school_id,
                    area_id=c.area_id,
                    window_start=window_start,
                    window_end=window_end,
                    report_count=c.window_count,
                    baseline_count=c.expected,
                    score=c.score,
                )
            )
            created += 1
    db.commit()
    return created, updated


def can_transition(current: SignalStatus, target: SignalStatus) -> bool:
    return target in TRANSITIONS.get(current, set())
