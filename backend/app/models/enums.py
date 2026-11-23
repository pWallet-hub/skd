"""All enumerations used by the domain. Stored in the database as plain strings."""

from enum import StrEnum

from sqlalchemy import Enum as SAEnum


def db_enum(enum_cls: type[StrEnum]) -> SAEnum:
    """Store enums as VARCHAR (not native PG enums) so adding values needs no migration."""
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=32,
        values_callable=lambda e: [m.value for m in e],
        validate_strings=True,
    )


class UserRole(StrEnum):
    PARENT = "parent"
    HEALTH_REVIEWER = "health_reviewer"  # validates health content, reviews signals
    ANALYST = "analyst"  # community intelligence, investigations
    INSTITUTION = "institution"  # aggregated read-only access for partner institutions
    ADMIN = "admin"


class AreaLevel(StrEnum):
    PROVINCE = "province"
    DISTRICT = "district"
    SECTOR = "sector"
    CELL = "cell"
    VILLAGE = "village"


class FacilityType(StrEnum):
    HOSPITAL = "hospital"
    HEALTH_CENTER = "health_center"
    HEALTH_POST = "health_post"
    CLINIC = "clinic"
    PHARMACY = "pharmacy"


class InfrastructureType(StrEnum):
    WATER_SOURCE = "water_source"
    WATER_POINT = "water_point"
    SANITATION = "sanitation"
    MARKET = "market"
    OTHER = "other"


class Sex(StrEnum):
    FEMALE = "female"
    MALE = "male"
    UNSPECIFIED = "unspecified"


class SymptomCategory(StrEnum):
    GASTROINTESTINAL = "gastrointestinal"
    RESPIRATORY = "respiratory"
    FEVER = "fever"
    SKIN = "skin"
    GENERAL = "general"


class ReportVerification(StrEnum):
    """A parent's observation is never treated as a diagnosis."""

    PARENT_OBSERVATION = "parent_observation"
    CLINICALLY_CONFIRMED = "clinically_confirmed"


class SignalStatus(StrEnum):
    DETECTED = "detected"
    UNDER_REVIEW = "under_review"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"


class AlertSeverity(StrEnum):
    INFO = "info"
    ADVISORY = "advisory"
    WARNING = "warning"


class AlertStatus(StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PUBLISHED = "published"
    RETRACTED = "retracted"


class NotificationKind(StrEnum):
    REMINDER = "reminder"
    GUIDANCE = "guidance"
    FOLLOW_UP = "follow_up"
    COMMUNITY_ALERT = "community_alert"
    SYSTEM = "system"


class ContentCategory(StrEnum):
    PARENTING = "parenting"
    NUTRITION = "nutrition"
    DEVELOPMENT = "development"
    HEALTH = "health"
    SAFETY = "safety"
    LEARNING = "learning"


class ContentAudience(StrEnum):
    PARENT = "parent"
    CHILD = "child"


class ContentStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"
