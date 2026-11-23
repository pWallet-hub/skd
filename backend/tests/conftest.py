"""Tests run against a separate PostGIS database (POSTGRES_TEST_DB), recreated per session."""

from collections.abc import Callable, Generator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app import models  # noqa: F401
from app.core.config import settings

settings.bcrypt_rounds = 4  # fast hashing in tests
from app.core.database import Base, get_db
from app.core.security import create_token, hash_password
from app.main import app
from app.models import AdministrativeArea, Child, School, Symptom, SymptomReport, User
from app.models.enums import AreaLevel, SymptomCategory, UserRole
from app.schemas.common import LatLng

engine = create_engine(settings.test_database_url)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def _schema() -> Generator[None, None, None]:
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    session = TestingSession()
    yield session
    session.close()
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db: Session) -> Callable[..., User]:
    counter = iter(range(1, 10_000))

    def _make(role: UserRole = UserRole.PARENT, **kwargs) -> User:
        user = User(
            email=kwargs.pop("email", f"user{next(counter)}@example.com"),
            full_name=kwargs.pop("full_name", "Test User"),
            password_hash=hash_password(kwargs.pop("password", "password123")),
            role=role,
            **kwargs,
        )
        db.add(user)
        db.commit()
        return user

    return _make


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(user.id, 'access')}"}


@pytest.fixture
def geo(db: Session) -> dict:
    """A minimal area/school/symptom setup."""
    district = AdministrativeArea(code="D1", name="District", level=AreaLevel.DISTRICT)
    sector = AdministrativeArea(
        code="S1",
        name="Sector",
        level=AreaLevel.SECTOR,
        parent=district,
        centroid=LatLng(latitude=-1.95, longitude=30.1).to_geometry(),
    )
    school = School(
        name="Test School",
        area=sector,
        location=LatLng(latitude=-1.95, longitude=30.1).to_geometry(),
    )
    diarrhea = Symptom(code="diarrhea", name="Diarrhea", category=SymptomCategory.GASTROINTESTINAL)
    cough = Symptom(code="cough", name="Cough", category=SymptomCategory.RESPIRATORY)
    db.add_all([district, sector, school, diarrhea, cough])
    db.commit()
    return {
        "district": district,
        "sector": sector,
        "school": school,
        "diarrhea": diarrhea,
        "cough": cough,
    }


@pytest.fixture
def add_reports(db: Session, make_user, geo) -> Callable[..., list[SymptomReport]]:
    def _add(count: int, days_ago: int = 0, symptom: Symptom | None = None) -> list[SymptomReport]:
        reports = []
        for i in range(count):
            parent = make_user(UserRole.PARENT)
            child = Child(
                guardian=parent,
                display_name=f"Child {i}",
                date_of_birth=date(2019, 1, 1),
                school=geo["school"],
                area=geo["sector"],
            )
            report = SymptomReport(
                child=child,
                reported_by=parent,
                onset_date=date.today() - timedelta(days=days_ago),
                symptoms=[symptom or geo["diarrhea"]],
                school=geo["school"],
                area=geo["sector"],
            )
            db.add(report)
            reports.append(report)
        db.commit()
        return reports

    return _add
