"""Geographic reference data: administrative areas, schools, facilities, infrastructure.

All geometries are WGS84 (SRID 4326), i.e. longitude/latitude.
"""

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.models.enums import AreaLevel, FacilityType, InfrastructureType, db_enum

SRID = 4326


class AdministrativeArea(TimestampMixin, Base):
    """Province > District > Sector > Cell > Village hierarchy."""

    __tablename__ = "administrative_areas"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    level: Mapped[AreaLevel] = mapped_column(db_enum(AreaLevel), index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("administrative_areas.id", ondelete="CASCADE"), index=True
    )
    centroid = mapped_column(Geometry("POINT", srid=SRID), nullable=True)
    boundary = mapped_column(Geometry("MULTIPOLYGON", srid=SRID), nullable=True)

    parent: Mapped["AdministrativeArea | None"] = relationship(remote_side="AdministrativeArea.id")


class School(TimestampMixin, Base):
    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    area_id: Mapped[int | None] = mapped_column(
        ForeignKey("administrative_areas.id", ondelete="SET NULL"), index=True
    )
    location = mapped_column(Geometry("POINT", srid=SRID), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    area: Mapped[AdministrativeArea | None] = relationship()


class HealthFacility(TimestampMixin, Base):
    __tablename__ = "health_facilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    facility_type: Mapped[FacilityType] = mapped_column(db_enum(FacilityType))
    area_id: Mapped[int | None] = mapped_column(
        ForeignKey("administrative_areas.id", ondelete="SET NULL"), index=True
    )
    location = mapped_column(Geometry("POINT", srid=SRID), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(32))
    opening_hours: Mapped[str | None] = mapped_column(String(120))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    area: Mapped[AdministrativeArea | None] = relationship()


class InfrastructureAsset(TimestampMixin, Base):
    """Context for investigations (water, sanitation...). Never evidence of a cause by itself."""

    __tablename__ = "infrastructure_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    asset_type: Mapped[InfrastructureType] = mapped_column(db_enum(InfrastructureType))
    area_id: Mapped[int | None] = mapped_column(
        ForeignKey("administrative_areas.id", ondelete="SET NULL"), index=True
    )
    location = mapped_column(Geometry("POINT", srid=SRID), nullable=True)
    data_source: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)

    area: Mapped[AdministrativeArea | None] = relationship()
