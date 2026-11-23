"""Import every model here so SQLAlchemy and Alembic see the full metadata."""

from app.models.content import Article
from app.models.family import Child, GrowthMeasurement
from app.models.geo import AdministrativeArea, HealthFacility, InfrastructureAsset, School
from app.models.health import Symptom, SymptomReport, report_symptoms
from app.models.notification import CommunityAlert, Notification
from app.models.surveillance import HealthSignal, InvestigationNote
from app.models.user import User

__all__ = [
    "AdministrativeArea",
    "Article",
    "Child",
    "CommunityAlert",
    "GrowthMeasurement",
    "HealthFacility",
    "HealthSignal",
    "InfrastructureAsset",
    "InvestigationNote",
    "Notification",
    "School",
    "Symptom",
    "SymptomReport",
    "User",
    "report_symptoms",
]
