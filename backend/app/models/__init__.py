"""Import every model here so SQLAlchemy and Alembic see the full metadata."""

from app.models.admin import AuditLog, SystemSetting
from app.models.child_health import ImmunizationRecord, MilestoneRecord
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
    "AuditLog",
    "Child",
    "CommunityAlert",
    "GrowthMeasurement",
    "HealthFacility",
    "HealthSignal",
    "ImmunizationRecord",
    "InfrastructureAsset",
    "InvestigationNote",
    "MilestoneRecord",
    "Notification",
    "School",
    "Symptom",
    "SymptomReport",
    "SystemSetting",
    "User",
    "report_symptoms",
]
