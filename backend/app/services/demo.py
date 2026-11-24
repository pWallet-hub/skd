"""Demo activity simulator — makes the FICTIONAL demo community behave like real users.

When demo mode is on (admin Settings, or DEMO_MODE=true), a Celery beat task calls
`simulate_activity` every few minutes. Each run does a handful of realistic things:

  * parents report new symptoms (respiratory/fever most common; some gastro around the
    demo cluster school so the community-signal story keeps developing)
  * children recover from earlier reports
  * parents record growth measurements, vaccinations and milestones
  * occasionally a new family signs up

Everything goes through the same service functions the API uses, so notifications,
statistics and signal detection behave exactly as they would with real users.
Only data belonging to demo accounts (…@example.com) is touched.
"""

import random
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    AdministrativeArea,
    Child,
    GrowthMeasurement,
    ImmunizationRecord,
    MilestoneRecord,
    School,
    Symptom,
    SymptomReport,
    User,
)
from app.models.enums import AreaLevel, Sex, UserRole
from app.services.child_health import MILESTONES, VACCINES, milestone_status, vaccine_status
from app.services.reports import create_report
from app.services.surveillance import detect_signals

DEMO_EMAIL_DOMAIN = "@example.com"
DEMO_PASSWORD = "SmartKids123!"
CLUSTER_SCHOOL_PREFIX = "Umucyo"
LAST_RUN_KEY = "demo_last_run"

FIRST_NAMES = [
    "Alice",
    "Jean",
    "Claudine",
    "Eric",
    "Diane",
    "Patrick",
    "Grace",
    "Olivier",
    "Solange",
    "Emmanuel",
    "Josiane",
    "Fabrice",
    "Vestine",
    "Innocent",
    "Chantal",
    "Theogene",
    "Delphine",
    "Celestin",
    "Esperance",
    "Aimable",
    "Francine",
    "Gilbert",
    "Immaculee",
    "Janvier",
]
LAST_NAMES = [
    "Uwase",
    "Habimana",
    "Mukamana",
    "Niyonzima",
    "Ingabire",
    "Mugisha",
    "Uwimana",
    "Nshimiyimana",
    "Umutoni",
    "Hakizimana",
    "Nyirahabimana",
    "Ndayisaba",
    "Mukeshimana",
    "Twagirayezu",
    "Uwamahoro",
    "Bizimana",
    "Iradukunda",
    "Munyaneza",
]
CHILD_NAMES = [
    "Keza",
    "Ganza",
    "Shema",
    "Teta",
    "Ineza",
    "Hirwa",
    "Gisa",
    "Mutesi",
    "Ishimwe",
    "Isimbi",
    "Cyusa",
    "Kalisa",
    "Umwari",
    "Bwiza",
    "Manzi",
    "Ikirezi",
    "Ntwari",
    "Gaju",
    "Kirezi",
    "Mugabo",
    "Nziza",
    "Rukundo",
    "Umutesi",
    "Gatete",
]
INTERESTS = ["reading", "music", "drawing", "numbers", "nature", "dancing", "football", "stories"]

# Typical everyday mix of complaints (weights), by symptom code.
EVERYDAY_SYMPTOMS = {
    "cough": 6,
    "runny_nose": 6,
    "fever": 5,
    "loss_of_appetite": 2,
    "fatigue": 2,
    "skin_rash": 2,
    "diarrhea": 2,
    "stomach_pain": 2,
    "vomiting": 1,
}


def _demo_children(db: Session) -> list[Child]:
    return list(
        db.scalars(
            select(Child)
            .join(User, User.id == Child.guardian_id)
            .where(User.email.endswith(DEMO_EMAIL_DOMAIN), User.role == UserRole.PARENT)
        )
    )


def _report(db: Session, rng: random.Random, child: Child, codes: list[str], today: date) -> None:
    symptoms = list(db.scalars(select(Symptom).where(Symptom.code.in_(codes))))
    if not symptoms:
        return
    create_report(
        db,
        child=child,
        reporter=child.guardian,
        symptoms=symptoms,
        onset_date=today - timedelta(days=rng.choice([0, 0, 1])),
        visited_facility=rng.random() < 0.3,
        notes="Simulated demo activity.",
    )


def _new_family(db: Session, rng: random.Random, today: date) -> User | None:
    sectors = list(
        db.scalars(select(AdministrativeArea).where(AdministrativeArea.level == AreaLevel.SECTOR))
    )
    if not sectors:
        return None
    sector = rng.choice(sectors)
    schools = list(db.scalars(select(School).where(School.area_id == sector.id))) or list(
        db.scalars(select(School))
    )
    n = 1
    while db.scalar(select(User.id).where(User.email == f"family{n}{DEMO_EMAIL_DOMAIN}")):
        n += 1
    parent = User(
        email=f"family{n}{DEMO_EMAIL_DOMAIN}",
        full_name=f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
        role=UserRole.PARENT,
        password_hash=hash_password(DEMO_PASSWORD),
        home_area_id=sector.id,
        phone_number=f"+250 78{rng.randint(1000000, 9999999)}",
    )
    db.add(parent)
    db.flush()
    for _ in range(rng.choice([1, 1, 2])):
        dob = today - timedelta(days=rng.randint(120, 365 * 9))
        db.add(
            Child(
                guardian_id=parent.id,
                display_name=rng.choice(CHILD_NAMES),
                date_of_birth=dob,
                sex=rng.choice([Sex.FEMALE, Sex.MALE]),
                area_id=sector.id,
                school_id=rng.choice(schools).id
                if schools and (today - dob).days > 3 * 365
                else None,
                learning_interests=rng.sample(INTERESTS, 2),
            )
        )
    return parent


def simulate_activity(db: Session, seed: int | None = None) -> dict[str, int]:
    """One round of realistic demo activity. Returns counts of what happened."""
    rng = random.Random(seed)
    today = date.today()
    children = _demo_children(db)
    stats = {"reports": 0, "recoveries": 0, "measurements": 0, "vaccinations": 0,
             "milestones": 0, "new_families": 0}  # fmt: skip
    if not children:
        return stats

    # 1) New symptom reports (1–3 everyday ones)
    codes, weights = zip(*EVERYDAY_SYMPTOMS.items(), strict=True)
    for child in rng.sample(children, k=min(len(children), rng.randint(1, 3))):
        picked = list(dict.fromkeys(rng.choices(codes, weights=weights, k=rng.choice([1, 2]))))
        _report(db, rng, child, picked, today)
        stats["reports"] += 1

    # 2) Keep the demo cluster story alive: gastro reports around the cluster school
    cluster = [c for c in children if c.school and c.school.name.startswith(CLUSTER_SCHOOL_PREFIX)]
    if cluster and rng.random() < 0.5:
        _report(
            db,
            rng,
            rng.choice(cluster),
            rng.sample(["diarrhea", "stomach_pain", "vomiting"], 2),
            today,
        )
        stats["reports"] += 1

    # 3) Some children recover
    ongoing = list(
        db.scalars(
            select(SymptomReport)
            .where(
                SymptomReport.is_ongoing.is_(True),
                SymptomReport.onset_date <= today - timedelta(days=2),
            )
            .limit(50)
        )
    )
    for report in rng.sample(ongoing, k=min(len(ongoing), rng.randint(0, 3))):
        report.is_ongoing = False
        report.recovered_on = today
        stats["recoveries"] += 1

    # 4) Growth measurements, vaccinations, milestones
    for child in rng.sample(children, k=min(len(children), rng.randint(1, 2))):
        last = child.measurements[-1] if child.measurements else None
        if last and last.measured_on >= today - timedelta(days=14):
            continue
        age_years = (today - child.date_of_birth).days / 365
        db.add(
            GrowthMeasurement(
                child_id=child.id,
                measured_on=today,
                height_cm=round(
                    (float(last.height_cm) + rng.uniform(0.3, 1.5))
                    if last and last.height_cm
                    else 50 + age_years * 9,
                    1,
                ),
                weight_kg=round(
                    (float(last.weight_kg) + rng.uniform(0.05, 0.5))
                    if last and last.weight_kg
                    else 3.3 + age_years * 2.3,
                    2,
                ),
            )
        )
        stats["measurements"] += 1

    for child in rng.sample(children, k=min(len(children), 3)):
        given = set(
            db.scalars(
                select(ImmunizationRecord.vaccine_code).where(
                    ImmunizationRecord.child_id == child.id
                )
            )
        )
        due = [
            v
            for v in VACCINES
            if v.code not in given
            and vaccine_status(child.date_of_birth, None, v.code) in ("due", "overdue")
        ]
        if due and rng.random() < 0.5:
            db.add(ImmunizationRecord(child_id=child.id, vaccine_code=due[0].code, given_on=today))
            stats["vaccinations"] += 1
        reached = set(
            db.scalars(
                select(MilestoneRecord.milestone_code).where(MilestoneRecord.child_id == child.id)
            )
        )
        pending = [
            m
            for m in MILESTONES
            if m.code not in reached
            and milestone_status(child.date_of_birth, None, m.code) != "upcoming"
        ]
        if pending and rng.random() < 0.5:
            db.add(
                MilestoneRecord(
                    child_id=child.id, milestone_code=pending[0].code, achieved_on=today
                )
            )
            stats["milestones"] += 1

    # 5) Occasionally a new family joins
    if rng.random() < 0.25 and _new_family(db, rng, today):
        stats["new_families"] += 1

    db.commit()
    detect_signals(db)
    record_last_run(db, stats)
    return stats


def record_last_run(db: Session, stats: dict[str, int]) -> None:
    from datetime import UTC, datetime

    from app.models import SystemSetting

    row = db.get(SystemSetting, LAST_RUN_KEY)
    value = {"at": datetime.now(UTC).isoformat(), "stats": stats}
    if row is None:
        db.add(SystemSetting(key=LAST_RUN_KEY, value=value))
    else:
        row.value = value
    db.commit()
