"""Immunization schedule and developmental milestones.

The schedule below is an EXAMPLE based on a typical routine childhood programme. It must be
reviewed and replaced with the national schedule by health professionals before real use.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Child, ImmunizationRecord, MilestoneRecord
from app.services.children import age_in_months


@dataclass(frozen=True)
class Vaccine:
    code: str
    name: str
    due_days: int  # age in days when the dose is due
    protects_against: str


VACCINES: tuple[Vaccine, ...] = (
    Vaccine("BCG", "BCG", 0, "Tuberculosis"),
    Vaccine("OPV0", "Polio (birth dose)", 0, "Polio"),
    Vaccine("OPV1", "Polio 1", 42, "Polio"),
    Vaccine("PENTA1", "Pentavalent 1", 42, "Diphtheria, tetanus, pertussis, hepatitis B, Hib"),
    Vaccine("PCV1", "Pneumococcal 1", 42, "Pneumonia, meningitis"),
    Vaccine("ROTA1", "Rotavirus 1", 42, "Rotavirus diarrhoea"),
    Vaccine("OPV2", "Polio 2", 70, "Polio"),
    Vaccine("PENTA2", "Pentavalent 2", 70, "Diphtheria, tetanus, pertussis, hepatitis B, Hib"),
    Vaccine("PCV2", "Pneumococcal 2", 70, "Pneumonia, meningitis"),
    Vaccine("ROTA2", "Rotavirus 2", 70, "Rotavirus diarrhoea"),
    Vaccine("OPV3", "Polio 3", 98, "Polio"),
    Vaccine("PENTA3", "Pentavalent 3", 98, "Diphtheria, tetanus, pertussis, hepatitis B, Hib"),
    Vaccine("PCV3", "Pneumococcal 3", 98, "Pneumonia, meningitis"),
    Vaccine("IPV", "Inactivated polio", 98, "Polio"),
    Vaccine("MR1", "Measles–Rubella 1", 274, "Measles, rubella"),
    Vaccine("MR2", "Measles–Rubella 2", 456, "Measles, rubella"),
)
VACCINE_BY_CODE = {v.code: v for v in VACCINES}
OVERDUE_AFTER_DAYS = 28


@dataclass(frozen=True)
class Milestone:
    code: str
    title: str
    domain: Literal["social", "language", "movement", "thinking"]
    expected_months: int


MILESTONES: tuple[Milestone, ...] = (
    Milestone("smiles", "Smiles at people", "social", 2),
    Milestone("holds_head", "Holds head steady", "movement", 4),
    Milestone("babbles", "Babbles and makes sounds", "language", 6),
    Milestone("sits", "Sits without support", "movement", 9),
    Milestone("first_words", "Says “mama” or “dada”", "language", 12),
    Milestone("stands", "Pulls up to stand", "movement", 12),
    Milestone("walks", "Walks alone", "movement", 15),
    Milestone("points", "Points to show interest", "social", 18),
    Milestone("two_words", "Uses two-word phrases", "language", 24),
    Milestone("kicks_ball", "Kicks a ball", "movement", 24),
    Milestone("short_sentences", "Talks in short sentences", "language", 36),
    Milestone("plays_with_others", "Plays with other children", "social", 36),
    Milestone("tells_story", "Tells a simple story", "language", 48),
    Milestone("hops", "Hops on one foot", "movement", 48),
    Milestone("counts_10", "Counts to 10", "thinking", 60),
    Milestone("writes_name", "Writes some letters of their name", "thinking", 60),
)
MILESTONE_BY_CODE = {m.code: m for m in MILESTONES}
FOLLOW_UP_AFTER_MONTHS = 3

VaccineStatus = Literal["given", "due", "overdue", "upcoming"]
MilestoneStatus = Literal["achieved", "expected", "check", "upcoming"]


def vaccine_status(
    dob: date, given: date | None, code: str, today: date | None = None
) -> VaccineStatus:
    if given:
        return "given"
    today = today or date.today()
    due = dob + timedelta(days=VACCINE_BY_CODE[code].due_days)
    if today < due:
        return "upcoming"
    if (today - due).days > OVERDUE_AFTER_DAYS:
        return "overdue"
    return "due"


def milestone_status(
    dob: date, achieved: date | None, code: str, today: date | None = None
) -> MilestoneStatus:
    if achieved:
        return "achieved"
    months = age_in_months(dob, today)
    expected = MILESTONE_BY_CODE[code].expected_months
    if months < expected:
        return "upcoming"
    if months >= expected + FOLLOW_UP_AFTER_MONTHS:
        return "check"  # worth discussing with a health worker — not a diagnosis
    return "expected"


def immunization_schedule(db: Session, child: Child) -> list[dict]:
    records = {
        r.vaccine_code: r
        for r in db.scalars(
            select(ImmunizationRecord).where(ImmunizationRecord.child_id == child.id)
        )
    }
    items = []
    for v in VACCINES:
        rec = records.get(v.code)
        items.append(
            {
                "code": v.code,
                "name": v.name,
                "protects_against": v.protects_against,
                "due_date": child.date_of_birth + timedelta(days=v.due_days),
                "status": vaccine_status(
                    child.date_of_birth, rec.given_on if rec else None, v.code
                ),
                "given_on": rec.given_on if rec else None,
                "record_id": rec.id if rec else None,
            }
        )
    return items


def milestone_checklist(db: Session, child: Child) -> list[dict]:
    records = {
        r.milestone_code: r
        for r in db.scalars(select(MilestoneRecord).where(MilestoneRecord.child_id == child.id))
    }
    items = []
    for m in MILESTONES:
        rec = records.get(m.code)
        items.append(
            {
                "code": m.code,
                "title": m.title,
                "domain": m.domain,
                "expected_months": m.expected_months,
                "status": milestone_status(
                    child.date_of_birth, rec.achieved_on if rec else None, m.code
                ),
                "achieved_on": rec.achieved_on if rec else None,
                "record_id": rec.id if rec else None,
            }
        )
    return items


def care_summary(db: Session, child: Child) -> dict[str, int]:
    vaccines = immunization_schedule(db, child)
    milestones = milestone_checklist(db, child)
    return {
        "vaccines_due": sum(1 for v in vaccines if v["status"] in ("due", "overdue")),
        "vaccines_overdue": sum(1 for v in vaccines if v["status"] == "overdue"),
        "milestones_to_check": sum(1 for m in milestones if m["status"] == "check"),
    }
