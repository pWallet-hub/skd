"""Load FICTIONAL demo data. Safe to re-run (it wipes previous demo data first).

    make seed     # or: docker compose exec backend python -m app.scripts.seed

Administrative area names are real Kigali districts/sectors so the map looks right, but
every family, child, school, facility, infrastructure item and report is invented.
The data contains a deliberately injected cluster of gastrointestinal reports around one
school so the signal-detection workflow can be demonstrated. It is NOT a real health event.
"""

import random
from datetime import date, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import (
    AdministrativeArea,
    Article,
    Child,
    CommunityAlert,
    GrowthMeasurement,
    HealthFacility,
    HealthSignal,
    InfrastructureAsset,
    Notification,
    School,
    Symptom,
    SymptomReport,
    User,
)
from app.models.enums import (
    AreaLevel,
    ContentAudience,
    ContentCategory,
    ContentStatus,
    FacilityType,
    InfrastructureType,
    NotificationKind,
    Sex,
    SymptomCategory,
    UserRole,
)
from app.schemas.common import LatLng
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

ARTICLES = [
    (
        "handwashing-at-home",
        "Handwashing habits that protect the whole family",
        "Simple, age-appropriate ways to build handwashing routines.",
        ContentCategory.HEALTH,
    ),
    (
        "balanced-meals-under-five",
        "Balanced meals for children under five",
        "Practical meal ideas using locally available foods.",
        ContentCategory.NUTRITION,
    ),
    (
        "when-to-seek-care-diarrhea",
        "Diarrhea: when to seek medical care",
        "Warning signs that mean your child should see a health worker.",
        ContentCategory.HEALTH,
    ),
    (
        "reading-together",
        "Reading together every day",
        "Why ten minutes of shared reading matters for development.",
        ContentCategory.DEVELOPMENT,
    ),
]

PARENT_NAMES = [
    "Aline Uwase",
    "Jean Bosco Habimana",
    "Claudine Mukamana",
    "Eric Niyonzima",
    "Diane Ingabire",
    "Patrick Mugisha",
    "Grace Uwimana",
    "Olivier Nshimiyimana",
    "Solange Umutoni",
    "Emmanuel Hakizimana",
    "Josiane Nyirahabimana",
    "Fabrice Ndayisaba",
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
]


def wipe(db: Session) -> None:
    for model in (
        Notification,
        CommunityAlert,
        HealthSignal,
        SymptomReport,
        GrowthMeasurement,
        Child,
        Article,
        User,
        InfrastructureAsset,
        HealthFacility,
        School,
        Symptom,
        AdministrativeArea,
    ):
        db.execute(delete(model))
    db.commit()


def seed(db: Session) -> None:
    wipe(db)
    today = date.today()

    symptoms = {code: Symptom(code=code, name=name, category=cat) for code, name, cat in SYMPTOMS}
    db.add_all(symptoms.values())

    kigali = AdministrativeArea(
        code="KGL", name="Kigali City", level=AreaLevel.PROVINCE, centroid=pt(-1.9441, 30.0619)
    )
    db.add(kigali)
    sectors: dict[str, AdministrativeArea] = {}
    for code, name, lat, lng, children in AREAS[1:]:
        district = AdministrativeArea(
            code=code, name=name, level=AreaLevel.DISTRICT, parent=kigali, centroid=pt(lat, lng)
        )
        db.add(district)
        for s_code, s_name, s_lat, s_lng in children:
            sectors[s_code] = AdministrativeArea(
                code=s_code,
                name=s_name,
                level=AreaLevel.SECTOR,
                parent=district,
                centroid=pt(s_lat, s_lng),
            )
            db.add(sectors[s_code])

    schools = [
        School(name=n, area=sectors[a], location=pt(lat, lng), is_verified=True)
        for n, a, lat, lng in SCHOOLS
    ]
    db.add_all(schools)
    db.add_all(
        HealthFacility(
            name=n,
            facility_type=t,
            area=sectors[a],
            location=pt(lat, lng),
            phone_number="+250 700 000 000",
            opening_hours="Mon–Sat 07:00–19:00",
            is_verified=True,
        )
        for n, t, a, lat, lng in FACILITIES
    )
    db.add_all(
        InfrastructureAsset(
            name=n,
            asset_type=t,
            area=sectors[a],
            location=pt(lat, lng),
            data_source="Fictional demo dataset",
        )
        for n, t, a, lat, lng in INFRASTRUCTURE
    )

    pw = hash_password(DEMO_PASSWORD)
    staff = [
        User(
            email="admin@example.com",
            full_name="Demo Administrator",
            role=UserRole.ADMIN,
            password_hash=pw,
        ),
        User(
            email="reviewer@example.com",
            full_name="Dr. Demo Reviewer",
            role=UserRole.HEALTH_REVIEWER,
            password_hash=pw,
        ),
        User(
            email="analyst@example.com",
            full_name="Demo Analyst",
            role=UserRole.ANALYST,
            password_hash=pw,
        ),
        User(
            email="institution@example.com",
            full_name="Demo Partner Institution",
            role=UserRole.INSTITUTION,
            password_hash=pw,
        ),
    ]
    db.add_all(staff)
    reviewer = staff[1]

    for slug, title, summary, cat in ARTICLES:
        db.add(
            Article(
                slug=slug,
                title=title,
                summary=summary,
                category=cat,
                body=f"{summary}\n\n(Demo article body. Replace with content reviewed by a health professional.)",
                audience=ContentAudience.PARENT,
                status=ContentStatus.PUBLISHED,
                reviewed_by=reviewer,
                published_at=None,
            )
        )

    # Families -------------------------------------------------------------
    sector_list = list(sectors.values())
    school_by_sector = {s.area.code: s for s in schools}
    children: list[Child] = []
    for i, name in enumerate(PARENT_NAMES):
        email = "parent@example.com" if i == 0 else f"parent{i + 1}@example.com"
        # First 5 families live in Kimironko and use the "cluster" school.
        sector = sectors["GAS-KIM"] if i < 5 else sector_list[i % len(sector_list)]
        parent = User(
            email=email,
            full_name=name,
            role=UserRole.PARENT,
            password_hash=pw,
            home_area=sector,
            phone_number=f"+250 78{i:07d}",
        )
        db.add(parent)
        for _ in range(rng.choice([1, 2, 2])):
            dob = today - timedelta(days=rng.randint(365, 365 * 10))
            child = Child(
                guardian=parent,
                display_name=CHILD_NAMES[len(children) % len(CHILD_NAMES)],
                date_of_birth=dob,
                sex=rng.choice([Sex.FEMALE, Sex.MALE]),
                area=sector,
                school=school_by_sector.get(sector.code, rng.choice(schools)),
                learning_interests=rng.sample(
                    ["reading", "music", "drawing", "numbers", "nature"], 2
                ),
            )
            for m in range(4):
                child.measurements.append(
                    GrowthMeasurement(
                        measured_on=today - timedelta(days=90 * (3 - m)),
                        height_cm=round(75 + (today - dob).days / 365 * 7 + m, 1),
                        weight_kg=round(9 + (today - dob).days / 365 * 2.2 + m * 0.3, 2),
                    )
                )
            db.add(child)
            children.append(child)
    db.flush()

    # Background reports over the last ~45 days ----------------------------
    sym_list = list(symptoms.values())
    for _ in range(45):
        child = rng.choice(children)
        onset = today - timedelta(days=rng.randint(8, 45))
        db.add(
            SymptomReport(
                child=child,
                reported_by=child.guardian,
                onset_date=onset,
                symptoms=rng.sample(sym_list, rng.choice([1, 1, 2])),
                school=child.school,
                area=child.area,
                is_ongoing=False,
                recovered_on=onset + timedelta(days=rng.randint(1, 5)),
            )
        )

    # Injected cluster: gastro symptoms at the Kimironko school, last 6 days
    cluster_children = [c for c in children if c.area.code == "GAS-KIM"]
    gastro = [symptoms["diarrhea"], symptoms["stomach_pain"], symptoms["vomiting"]]
    for i, child in enumerate(cluster_children):
        db.add(
            SymptomReport(
                child=child,
                reported_by=child.guardian,
                onset_date=today - timedelta(days=i % 6),
                symptoms=rng.sample(gastro, 2),
                school=child.school,
                area=child.area,
                visited_facility=i % 2 == 0,
                notes="Demo data: part of the injected cluster.",
            )
        )

    # A few personal notifications for the main demo parent
    main_parent = db.scalar(select(User).where(User.email == "parent@example.com"))
    db.add_all(
        [
            Notification(
                recipient=main_parent,
                kind=NotificationKind.REMINDER,
                title="Time to record growth",
                body="It has been 3 months since the last measurement.",
            ),
            Notification(
                recipient=main_parent,
                kind=NotificationKind.GUIDANCE,
                title="New article: Handwashing habits",
                body="A short guide for the whole family.",
            ),
        ]
    )
    db.commit()

    created, updated = detect_signals(db)
    print(f"Seeded demo data. Signals detected: {created} created, {updated} updated.")
    print(f"Demo password for every account: {DEMO_PASSWORD}")
    print("Accounts: parent@ / reviewer@ / analyst@ / institution@ / admin@ example.com")


def main() -> None:
    with SessionLocal() as db:
        seed(db)


if __name__ == "__main__":
    main()
