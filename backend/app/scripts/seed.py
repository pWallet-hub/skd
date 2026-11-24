"""Load FICTIONAL demo data. Safe to re-run (it wipes previous demo data first).

    make seed     # or: docker compose exec backend python -m app.scripts.seed

Modes:
  (none)      wipe and re-seed now
  --if-empty  only seed a database that has no users
  --auto      used on every deploy when SEED_DEMO_DATA=true: seed an empty database, and
              REFRESH the demo data when DEMO_DATA_VERSION changes — but only if every account
              is a demo account (@example.com). Real users' data is never touched.

Administrative area names are real Kigali districts/sectors so the map looks right, but
every family, child, school, facility, infrastructure item and report is invented.
The data contains a deliberately injected cluster of gastrointestinal reports around one
school so the signal-detection workflow can be demonstrated. It is NOT a real health event.
"""

import argparse
import random
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import (
    AdministrativeArea,
    Article,
    AuditLog,
    Child,
    CommunityAlert,
    GrowthMeasurement,
    HealthFacility,
    HealthSignal,
    ImmunizationRecord,
    InfrastructureAsset,
    InvestigationNote,
    MilestoneRecord,
    Notification,
    School,
    Symptom,
    SymptomReport,
    SystemSetting,
    User,
)
from app.models.enums import (
    AlertSeverity,
    AlertStatus,
    AreaLevel,
    ContentAudience,
    ContentCategory,
    ContentStatus,
    FacilityType,
    InfrastructureType,
    NotificationKind,
    ReportVerification,
    Sex,
    SignalStatus,
    SymptomCategory,
    UserRole,
)
from app.schemas.common import LatLng
from app.services.child_health import MILESTONES, VACCINES
from app.services.demo import CHILD_NAMES, FIRST_NAMES, INTERESTS, LAST_NAMES
from app.services.surveillance import detect_signals

DEMO_PASSWORD = "SmartKids123!"
rng = random.Random(42)


def pt(lat: float, lng: float):
    return LatLng(latitude=lat, longitude=lng).to_geometry()


SYMPTOMS = [
    ("diarrhea", "Diarrhea", SymptomCategory.GASTROINTESTINAL),
    ("vomiting", "Vomiting", SymptomCategory.GASTROINTESTINAL),
    ("stomach_pain", "Stomach pain", SymptomCategory.GASTROINTESTINAL),
    ("cough", "Coughing", SymptomCategory.RESPIRATORY),
    ("runny_nose", "Runny nose", SymptomCategory.RESPIRATORY),
    ("breathing_difficulty", "Difficulty breathing", SymptomCategory.RESPIRATORY),
    ("fever", "Fever", SymptomCategory.FEVER),
    ("skin_rash", "Skin rash or irritation", SymptomCategory.SKIN),
    ("loss_of_appetite", "Loss of appetite", SymptomCategory.GENERAL),
    ("fatigue", "Unusual tiredness", SymptomCategory.GENERAL),
    ("other", "Other concern", SymptomCategory.GENERAL),
]

# (district code, district, lat, lng, [(sector code, sector, lat, lng), ...])
AREAS = [
    ("KGL", "Kigali City", -1.9441, 30.0619, []),
    (
        "GAS",
        "Gasabo",
        -1.9000,
        30.1100,
        [
            ("GAS-KIM", "Kimironko", -1.9497, 30.1258),
            ("GAS-REM", "Remera", -1.9578, 30.1094),
            ("GAS-KAC", "Kacyiru", -1.9373, 30.0874),
        ],
    ),
    (
        "KIC",
        "Kicukiro",
        -1.9850,
        30.1000,
        [
            ("KIC-KIC", "Kicukiro", -1.9706, 30.1044),
            ("KIC-NIB", "Niboye", -1.9810, 30.1180),
            ("KIC-GIK", "Gikondo", -1.9770, 30.0760),
        ],
    ),
    (
        "NYA",
        "Nyarugenge",
        -1.9500,
        30.0450,
        [
            ("NYA-NYA", "Nyamirambo", -1.9789, 30.0436),
            ("NYA-MUH", "Muhima", -1.9426, 30.0570),
            ("NYA-NYG", "Nyarugenge", -1.9491, 30.0589),
        ],
    ),
]

# Fictional schools: (name, sector code, lat, lng)
SCHOOLS = [
    ("Umucyo Primary School (demo)", "GAS-KIM", -1.9470, 30.1290),
    ("Inyange Primary School (demo)", "GAS-REM", -1.9590, 30.1120),
    ("Akeza Nursery School (demo)", "KIC-NIB", -1.9830, 30.1150),
    ("Ishema Primary School (demo)", "KIC-GIK", -1.9750, 30.0790),
    ("Urumuri Primary School (demo)", "NYA-NYA", -1.9760, 30.0410),
    ("Ubumwe Nursery School (demo)", "NYA-MUH", -1.9440, 30.0600),
]

FACILITIES = [
    ("Kimironko Health Centre (demo)", FacilityType.HEALTH_CENTER, "GAS-KIM", -1.9510, 30.1230),
    ("Remera Children's Clinic (demo)", FacilityType.CLINIC, "GAS-REM", -1.9560, 30.1060),
    ("Kicukiro District Hospital (demo)", FacilityType.HOSPITAL, "KIC-KIC", -1.9690, 30.1010),
    ("Gikondo Health Post (demo)", FacilityType.HEALTH_POST, "KIC-GIK", -1.9790, 30.0730),
    ("Nyamirambo Health Centre (demo)", FacilityType.HEALTH_CENTER, "NYA-NYA", -1.9800, 30.0460),
    ("Muhima Pharmacy (demo)", FacilityType.PHARMACY, "NYA-MUH", -1.9410, 30.0550),
]

INFRASTRUCTURE = [
    (
        "Kimironko public water point A (demo)",
        InfrastructureType.WATER_POINT,
        "GAS-KIM",
        -1.9460,
        30.1300,
    ),
    ("Kimironko market (demo)", InfrastructureType.MARKET, "GAS-KIM", -1.9505, 30.1265),
    ("Remera water reservoir (demo)", InfrastructureType.WATER_SOURCE, "GAS-REM", -1.9600, 30.1150),
    ("Niboye sanitation block (demo)", InfrastructureType.SANITATION, "KIC-NIB", -1.9820, 30.1200),
    (
        "Nyamirambo water point B (demo)",
        InfrastructureType.WATER_POINT,
        "NYA-NYA",
        -1.9775,
        30.0420,
    ),
]

# (slug, title, summary, category, body)
ARTICLES = [
    (
        "handwashing-at-home",
        "Handwashing habits that protect the whole family",
        "Simple, age-appropriate ways to build handwashing routines.",
        ContentCategory.HEALTH,
        "Wash hands with soap and clean water before eating, before preparing food, after using the "
        "toilet and after changing a nappy.\n\nFor young children, make it a song: wash for as long as "
        "it takes to sing a short song twice. Keep soap where children can reach it, and wash your own "
        "hands with them — children copy what they see.",
    ),
    (
        "balanced-meals-under-five",
        "Balanced meals for children under five",
        "Practical meal ideas using locally available foods.",
        ContentCategory.NUTRITION,
        "Each day, try to include a staple (sweet potato, cassava, rice, maize), a protein (beans, "
        "eggs, small fish, milk), and vegetables or fruit (amaranth, carrots, avocado, banana).\n\n"
        "Young children have small stomachs: offer 3 meals and 2 snacks. Add a little oil or avocado "
        "for energy. Clean water is the best drink.",
    ),
    (
        "when-to-seek-care-diarrhea",
        "Diarrhea: when to seek medical care",
        "Warning signs that mean your child should see a health worker.",
        ContentCategory.HEALTH,
        "Most diarrhea gets better in a few days. Keep giving fluids (ORS if available), keep "
        "breastfeeding, and keep feeding.\n\nGo to a health facility straight away if your child has "
        "blood in the stool, cannot drink, vomits everything, is very sleepy, has sunken eyes, or has "
        "had diarrhea for more than 14 days.",
    ),
    (
        "reading-together",
        "Reading together every day",
        "Why ten minutes of shared reading matters for development.",
        ContentCategory.DEVELOPMENT,
        "Reading together builds vocabulary, attention and a love of learning. You don't need many "
        "books: tell stories, name things in pictures, and let your child turn the pages.\n\nAsk "
        "simple questions — “What happens next?” — and praise every answer.",
    ),
    (
        "vaccines-on-time",
        "Why vaccines on time matter",
        "How the routine schedule protects your child at the ages they are most at risk.",
        ContentCategory.HEALTH,
        "Vaccines are timed to protect children when diseases are most dangerous for them. Keep your "
        "child's vaccination card safe and bring it to every visit.\n\nIf a dose was missed, it is not "
        "too late — talk to your health centre about catching up.",
    ),
    (
        "play-ideas-toddlers",
        "Play ideas for toddlers at home",
        "Everyday play that builds movement, language and thinking skills.",
        ContentCategory.DEVELOPMENT,
        "Stacking cups, sorting beans by colour, singing action songs and playing hide-and-seek all "
        "build important skills.\n\nTalk about what your child is doing while they play — it is one of "
        "the best ways to grow their language.",
    ),
    (
        "road-safety-school",
        "Walking to school safely",
        "Teaching children to cross roads and be seen.",
        ContentCategory.SAFETY,
        "Walk the route together first. Teach children to stop at the kerb, look both ways and listen "
        "before crossing, and to use crossings where they exist.\n\nBright clothing helps drivers see "
        "children, especially early in the morning.",
    ),
]

DRAFT_ARTICLES = [
    (
        "safe-sleep-for-babies",
        "Safe sleep for babies",
        "Positions and bedding that lower the risk of sleep accidents.",
        ContentCategory.SAFETY,
        "Draft: place babies on their back to sleep, on a firm flat surface, without pillows or loose "
        "blankets. (Awaiting review by a health professional.)",
    ),
    (
        "first-1000-days",
        "The first 1,000 days",
        "Why nutrition from pregnancy to age two shapes lifelong health.",
        ContentCategory.NUTRITION,
        "Draft: the first 1,000 days are a window for growth and brain development. "
        "(Awaiting review by a health professional.)",
    ),
]

NUM_FAMILIES = 30
# Bump this whenever the demo data changes; deployments with SEED_DEMO_DATA=true refresh automatically.
DEMO_DATA_VERSION = "2026-11-24.2"
DEMO_VERSION_KEY = "demo_data_version"
KIMIRONKO_FAMILIES = 6  # families around the demo-cluster school


# ---- helpers ----------------------------------------------------------------
def height_cm(months: float) -> float:
    """Rough average height curve (fictional data only)."""
    return (50 + 25 * min(months, 12) / 12 + 12 * max(0, min(months, 24) - 12) / 12
            + 7 * max(0, months - 24) / 12)  # fmt: skip


def weight_kg(months: float) -> float:
    return (3.3 + 6.5 * min(months, 12) / 12 + 2.5 * max(0, min(months, 24) - 12) / 12
            + 2.1 * max(0, months - 24) / 12)  # fmt: skip


def months_between(a: date, b: date) -> float:
    return (b - a).days / 30.44


def add_child_history(child: Child, today: date, complete: bool = False) -> None:
    """Growth measurements, vaccinations and milestones consistent with the child's age."""
    dob = child.date_of_birth
    age_m = months_between(dob, today)
    # growth: monthly under 1 year, every 3 months after (last 12 months)
    step = 1 if age_m < 12 else 3
    m = max(0.0, age_m - 12)
    noise_h, noise_w = rng.uniform(-2, 2), rng.uniform(-0.6, 0.6)
    while m <= age_m:
        measured = dob + timedelta(days=int(m * 30.44))
        if measured <= today:
            child.measurements.append(
                GrowthMeasurement(
                    measured_on=measured,
                    height_cm=round(height_cm(m) + noise_h * min(1, m / 12), 1),
                    weight_kg=round(max(2.5, weight_kg(m) + noise_w * min(1, m / 12)), 2),
                )
            )
        m += step
    # vaccinations: given within 2 weeks of the due date; a few missed for realism
    for v in VACCINES:
        due = dob + timedelta(days=v.due_days)
        if due > today - timedelta(days=3):
            continue
        if not complete and rng.random() < 0.07:
            continue  # missed dose → shows as overdue
        child.immunizations.append(
            ImmunizationRecord(
                vaccine_code=v.code, given_on=min(today, due + timedelta(days=rng.randint(0, 14)))
            )
        )
    # milestones reached around the expected age
    for ms in MILESTONES:
        if ms.expected_months > age_m - 0.5:
            continue
        if not complete and rng.random() < 0.05:
            continue
        achieved = dob + timedelta(days=int((ms.expected_months + rng.uniform(-1, 1)) * 30.44))
        child.milestones.append(
            MilestoneRecord(milestone_code=ms.code, achieved_on=min(today, achieved))
        )


def wipe(db: Session) -> None:
    for model in (
        AuditLog, SystemSetting, Notification, CommunityAlert, InvestigationNote, HealthSignal,
        SymptomReport, ImmunizationRecord, MilestoneRecord, GrowthMeasurement, Child, Article,
        User, InfrastructureAsset, HealthFacility, School, Symptom, AdministrativeArea,
    ):  # fmt: skip
        db.execute(delete(model))
    db.commit()


def seed(db: Session) -> None:
    wipe(db)
    today = date.today()
    now = datetime.now(UTC)

    symptoms = {code: Symptom(code=code, name=name, category=cat) for code, name, cat in SYMPTOMS}
    db.add_all(symptoms.values())

    # ---- geography --------------------------------------------------------
    kigali = AdministrativeArea(
        code="KGL", name="Kigali City", level=AreaLevel.PROVINCE, centroid=pt(-1.9441, 30.0619)
    )
    db.add(kigali)
    sectors: dict[str, AdministrativeArea] = {}
    for code, name, lat, lng, subs in AREAS[1:]:
        district = AdministrativeArea(
            code=code, name=name, level=AreaLevel.DISTRICT, parent=kigali, centroid=pt(lat, lng)
        )
        db.add(district)
        for s_code, s_name, s_lat, s_lng in subs:
            sectors[s_code] = AdministrativeArea(
                code=s_code, name=s_name, level=AreaLevel.SECTOR, parent=district,
                centroid=pt(s_lat, s_lng),
            )  # fmt: skip
            db.add(sectors[s_code])

    schools = [
        School(name=n, area=sectors[a], location=pt(lat, lng), is_verified=True)
        for n, a, lat, lng in SCHOOLS
    ]
    db.add_all(schools)
    school_by_sector = {s.area.code: s for s in schools}
    facilities = [
        HealthFacility(
            name=n,
            facility_type=t,
            area=sectors[a],
            location=pt(lat, lng),
            phone_number="+250 700 000 000",
            opening_hours="Mon–Sat 07:00–19:00",
            is_verified=True,
        )  # fmt: skip
        for n, t, a, lat, lng in FACILITIES
    ]
    db.add_all(facilities)
    db.add_all(
        InfrastructureAsset(
            name=n,
            asset_type=t,
            area=sectors[a],
            location=pt(lat, lng),
            data_source="Fictional demo dataset",
        )  # fmt: skip
        for n, t, a, lat, lng in INFRASTRUCTURE
    )

    # ---- staff ------------------------------------------------------------
    pw = hash_password(DEMO_PASSWORD)

    def staff_user(email: str, name: str, role: UserRole) -> User:
        return User(email=email, full_name=name, role=role, password_hash=pw,
                    created_at=now - timedelta(days=75), last_login_at=now - timedelta(hours=rng.randint(2, 48)))  # fmt: skip

    admin = staff_user("admin@example.com", "Demo Administrator", UserRole.ADMIN)
    reviewer = staff_user("reviewer@example.com", "Dr. Demo Reviewer", UserRole.HEALTH_REVIEWER)
    reviewer2 = staff_user("reviewer2@example.com", "Nurse Demo Reviewer", UserRole.HEALTH_REVIEWER)
    analyst = staff_user("analyst@example.com", "Demo Analyst", UserRole.ANALYST)
    institution = staff_user(
        "institution@example.com", "Demo Partner Institution", UserRole.INSTITUTION
    )
    db.add_all([admin, reviewer, reviewer2, analyst, institution])

    # ---- content ----------------------------------------------------------
    for i, (slug, title, summary, cat, body) in enumerate(ARTICLES):
        db.add(Article(slug=slug, title=title, summary=summary, category=cat, body=body,
                       audience=ContentAudience.PARENT, status=ContentStatus.PUBLISHED,
                       reviewed_by=reviewer, author=analyst,
                       published_at=now - timedelta(days=60 - i * 7)))  # fmt: skip
    for slug, title, summary, cat, body in DRAFT_ARTICLES:
        db.add(Article(slug=slug, title=title, summary=summary, category=cat, body=body,
                       audience=ContentAudience.PARENT, status=ContentStatus.IN_REVIEW,
                       author=analyst))  # fmt: skip

    # ---- families ---------------------------------------------------------
    sector_list = list(sectors.values())
    children: list[Child] = []

    # The main demo parent: designed so every parent feature has something to show.
    main_parent = User(
        email="parent@example.com", full_name="Aline Uwase", role=UserRole.PARENT,
        password_hash=pw, home_area=sectors["GAS-KIM"], phone_number="+250 788 000 001",
        created_at=now - timedelta(days=58), last_login_at=now - timedelta(days=1),
    )  # fmt: skip
    db.add(main_parent)
    keza = Child(  # 4 years old, attends the demo-cluster school
        guardian=main_parent, display_name="Keza",
        date_of_birth=today - timedelta(days=4 * 365 + 95), sex=Sex.FEMALE,
        area=sectors["GAS-KIM"], school=school_by_sector["GAS-KIM"],
        learning_interests=["drawing", "stories"],
    )  # fmt: skip
    ganza = Child(  # ~9 months: measles–rubella dose is due now, "sits" milestone expected
        guardian=main_parent, display_name="Ganza",
        date_of_birth=today - timedelta(days=280), sex=Sex.MALE,
        area=sectors["GAS-KIM"], learning_interests=["music"],
    )  # fmt: skip
    for c in (keza, ganza):
        add_child_history(c, today, complete=True)
        db.add(c)
        children.append(c)
    # Keza: "tells a story" not yet recorded → shows as expected; Ganza: hasn't sat yet.
    keza.milestones[:] = [m for m in keza.milestones if m.milestone_code != "tells_story"]
    ganza.milestones[:] = [m for m in ganza.milestones if m.milestone_code != "sits"]
    # Ganza's measles–rubella dose is due now (not yet given) → parent can record it in the demo.
    ganza.immunizations[:] = [v for v in ganza.immunizations if v.vaccine_code != "MR1"]

    for i in range(1, NUM_FAMILIES):
        sector = sectors["GAS-KIM"] if i < KIMIRONKO_FAMILIES else sector_list[i % len(sector_list)]
        parent = User(
            email=f"parent{i + 1}@example.com",
            full_name=f"{FIRST_NAMES[i % len(FIRST_NAMES)]} {LAST_NAMES[(i * 7) % len(LAST_NAMES)]}",
            role=UserRole.PARENT, password_hash=pw, home_area=sector,
            phone_number=f"+250 78{i:07d}",
            created_at=now - timedelta(days=rng.randint(1, 60), hours=rng.randint(0, 23)),
            last_login_at=now - timedelta(days=rng.randint(0, 20)) if rng.random() < 0.7 else None,
        )  # fmt: skip
        db.add(parent)
        for _ in range(rng.choice([1, 1, 2, 2, 3])):
            dob = today - timedelta(days=rng.randint(90, 365 * 10))
            school = school_by_sector.get(sector.code, rng.choice(schools))
            child = Child(
                guardian=parent, display_name=rng.choice(CHILD_NAMES), date_of_birth=dob,
                sex=rng.choice([Sex.FEMALE, Sex.MALE]), area=sector,
                school=school if (today - dob).days > 3 * 365 else None,
                learning_interests=rng.sample(INTERESTS, 2),
            )  # fmt: skip
            add_child_history(child, today)
            db.add(child)
            children.append(child)
    db.flush()

    # ---- 90 days of report history -----------------------------------------
    everyday = ["cough", "runny_nose", "fever", "cough", "runny_nose", "fever", "loss_of_appetite",
                "fatigue", "skin_rash", "diarrhea", "stomach_pain", "vomiting", "breathing_difficulty"]  # fmt: skip
    for _ in range(170):
        child = rng.choice(children)
        onset = today - timedelta(days=rng.randint(8, 90))
        if onset < child.date_of_birth:
            continue
        codes = list(dict.fromkeys(rng.sample(everyday, rng.choice([1, 1, 2]))))
        r = SymptomReport(
            child=child, reported_by=child.guardian, onset_date=onset,
            symptoms=[symptoms[c] for c in codes], school=child.school, area=child.area,
            is_ongoing=False, recovered_on=onset + timedelta(days=rng.randint(1, 6)),
            visited_facility=rng.random() < 0.35,
            verification=ReportVerification.CLINICALLY_CONFIRMED if rng.random() < 0.2 else ReportVerification.PARENT_OBSERVATION,
            created_at=datetime.combine(onset, datetime.min.time(), UTC) + timedelta(hours=rng.randint(7, 20)),
        )  # fmt: skip
        db.add(r)
    # A normal recent week across the city (some still ongoing)
    for _ in range(9):
        child = rng.choice([c for c in children if c.area.code != "GAS-KIM"])
        onset = today - timedelta(days=rng.randint(0, 6))
        db.add(SymptomReport(
            child=child, reported_by=child.guardian, onset_date=onset,
            symptoms=[symptoms[rng.choice(everyday[:8])]], school=child.school, area=child.area,
            is_ongoing=rng.random() < 0.6,
        ))  # fmt: skip

    # Injected cluster: gastro symptoms around the Kimironko school, last 6 days
    gastro = [symptoms["diarrhea"], symptoms["stomach_pain"], symptoms["vomiting"]]
    cluster_children = [c for c in children if c.area.code == "GAS-KIM" and c.school][:9]
    for i, child in enumerate(cluster_children):
        db.add(SymptomReport(
            child=child, reported_by=child.guardian, onset_date=today - timedelta(days=i % 6),
            symptoms=rng.sample(gastro, 2), school=child.school, area=child.area,
            visited_facility=i % 2 == 0, notes="Started after lunch at school.",
        ))  # fmt: skip
    # Ganza had a cold three weeks ago (recovered)
    db.add(SymptomReport(
        child=ganza, reported_by=main_parent, onset_date=today - timedelta(days=21),
        symptoms=[symptoms["runny_nose"], symptoms["cough"]], area=ganza.area,
        is_ongoing=False, recovered_on=today - timedelta(days=17),
    ))  # fmt: skip

    # ---- a past, fully handled investigation (history for analysts) ----------
    ishema = next(s for s in schools if s.name.startswith("Ishema"))
    past_start = today - timedelta(days=45)
    past = HealthSignal(
        symptom_category=SymptomCategory.RESPIRATORY, school=ishema,
        window_start=past_start, window_end=past_start + timedelta(days=6),
        report_count=7, baseline_count=1.5, score=4.67, status=SignalStatus.RESOLVED,
        assigned_to=analyst, detected_at=now - timedelta(days=38),
        findings="Seasonal cold outbreak in two classes. School improved ventilation and "
                 "hand-washing; cases returned to normal within two weeks.",
    )  # fmt: skip
    db.add(past)
    for days_ago, change, body, who in [
        (
            38,
            "detected->under_review",
            "Contacted school nurse; several pupils absent with cough.",
            analyst,
        ),
        (
            36,
            "under_review->confirmed",
            "Health centre confirmed a rise in respiratory infections.",
            reviewer,
        ),
        (24, "confirmed->resolved", "Reports back to baseline for 10 days. Closing.", reviewer),
    ]:
        db.add(InvestigationNote(signal=past, author=who, body=body, status_change=change,
                                 created_at=now - timedelta(days=days_ago)))  # fmt: skip
    past_alert = CommunityAlert(
        title="Coughs and colds at Ishema Primary School",
        message="Some pupils have coughs and colds. Keep children who are unwell at home, wash "
                "hands often and seek care if breathing becomes fast or difficult.",
        severity=AlertSeverity.ADVISORY, status=AlertStatus.PUBLISHED, signal=past,
        created_by=analyst, approved_by=reviewer, target_schools=[ishema],
        approved_at=now - timedelta(days=35), published_at=now - timedelta(days=35),
        created_at=now - timedelta(days=36),
    )  # fmt: skip
    db.add(past_alert)
    db.flush()
    ishema_parents = {c.guardian for c in children if c.school_id == ishema.id}
    for parent in ishema_parents:
        db.add(Notification(recipient=parent, kind=NotificationKind.COMMUNITY_ALERT,
                            title=past_alert.title, body=past_alert.message, alert=past_alert,
                            created_at=now - timedelta(days=35), read_at=now - timedelta(days=34)))  # fmt: skip

    # An alert written by the analyst, waiting for a health reviewer's approval
    db.add(CommunityAlert(
        title="Reminder: measles–rubella vaccination week",
        message="Free measles–rubella vaccination is available at all health centres this week "
                "for children aged 9 months and 15 months. Bring your child's vaccination card.",
        severity=AlertSeverity.INFO, status=AlertStatus.PENDING_APPROVAL, created_by=analyst,
        target_areas=[sectors["GAS-KIM"], sectors["GAS-REM"], sectors["KIC-NIB"]],
    ))  # fmt: skip

    # ---- the main parent's notifications --------------------------------------
    for title, body, kind, days_ago, read in [
        (
            "Ganza's measles–rubella vaccine is due",
            "Ganza is now 9 months old. Visit your health centre for the measles–rubella dose.",
            NotificationKind.REMINDER,
            0,
            False,
        ),
        (
            "Time to record Ganza's growth",
            "It has been a month since the last measurement.",
            NotificationKind.REMINDER,
            2,
            False,
        ),
        (
            "New article: Why vaccines on time matter",
            "A short guide for parents.",
            NotificationKind.GUIDANCE,
            9,
            True,
        ),
        (
            "Report received for Ganza",
            "Thank you. We recorded runny nose, coughing.",
            NotificationKind.FOLLOW_UP,
            21,
            True,
        ),
    ]:
        db.add(Notification(recipient=main_parent, kind=kind, title=title, body=body,
                            created_at=now - timedelta(days=days_ago),
                            read_at=(now - timedelta(days=days_ago - 1)) if read else None))  # fmt: skip
    db.commit()

    db.add(SystemSetting(key=DEMO_VERSION_KEY, value=DEMO_DATA_VERSION))
    db.commit()

    created, updated = detect_signals(db)
    print(f"Seeded demo data (version {DEMO_DATA_VERSION}): {NUM_FAMILIES} families, {len(children)} children. "
          f"Signals detected: {created} created, {updated} updated.")  # fmt: skip
    print(f"Demo password for every account: {DEMO_PASSWORD}")
    print(
        "Accounts: parent@ / reviewer@ / reviewer2@ / analyst@ / institution@ / admin@ example.com"
    )


def auto(db: Session) -> None:
    """Deploy-time behaviour for SEED_DEMO_DATA=true (see module docstring)."""
    users = db.scalar(select(func.count(User.id))) or 0
    if users == 0:
        print("Empty database: loading demo data.")
        seed(db)
        return
    real_users = db.scalar(select(func.count(User.id)).where(User.email.not_like("%@example.com")))
    if real_users:
        print(f"{real_users} non-demo account(s) present; demo data left untouched.")
        return
    current = db.get(SystemSetting, DEMO_VERSION_KEY)
    if current is not None and current.value == DEMO_DATA_VERSION:
        print(f"Demo data is up to date (version {DEMO_DATA_VERSION}).")
        return
    print(
        f"Refreshing demo data: {current.value if current else 'unversioned'} -> {DEMO_DATA_VERSION}"
    )
    seed(db)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load fictional demo data.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--if-empty", action="store_true", help="Only seed a database with no users."
    )
    group.add_argument(
        "--auto", action="store_true", help="Deploy-time mode (see module docstring)."
    )
    args = parser.parse_args()
    with SessionLocal() as db:
        if args.auto:
            auto(db)
            return
        if args.if_empty and db.scalar(select(func.count(User.id))):
            print("Database already has users; skipping demo seed.")
            return
        seed(db)


if __name__ == "__main__":
    main()
