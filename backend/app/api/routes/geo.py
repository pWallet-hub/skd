from fastapi import APIRouter, Query
from geoalchemy2 import Geography
from sqlalchemy import cast, func, select

from app.api.deps import CurrentUser, DbSession
from app.models import AdministrativeArea, HealthFacility, InfrastructureAsset, School
from app.models.enums import AreaLevel, FacilityType, InfrastructureType
from app.schemas.common import LatLng
from app.schemas.geo import (
    AreaRead,
    FacilityNearby,
    FacilityRead,
    InfrastructureRead,
    SchoolRead,
)

router = APIRouter(prefix="/geo", tags=["geography"])


@router.get("/areas", response_model=list[AreaRead])
def list_areas(
    db: DbSession,
    level: AreaLevel | None = None,
    parent_id: int | None = None,
) -> list[AdministrativeArea]:
    """Public: used during registration to pick a home area."""
    stmt = select(AdministrativeArea).order_by(AdministrativeArea.name)
    if level:
        stmt = stmt.where(AdministrativeArea.level == level)
    if parent_id is not None:
        stmt = stmt.where(AdministrativeArea.parent_id == parent_id)
    return list(db.scalars(stmt))


@router.get("/schools", response_model=list[SchoolRead])
def list_schools(db: DbSession, _: CurrentUser, area_id: int | None = None) -> list[School]:
    stmt = select(School).order_by(School.name)
    if area_id is not None:
        stmt = stmt.where(School.area_id == area_id)
    return list(db.scalars(stmt))


@router.get("/facilities", response_model=list[FacilityRead])
def list_facilities(
    db: DbSession,
    _: CurrentUser,
    facility_type: FacilityType | None = None,
    area_id: int | None = None,
) -> list[HealthFacility]:
    stmt = select(HealthFacility).order_by(HealthFacility.name)
    if facility_type:
        stmt = stmt.where(HealthFacility.facility_type == facility_type)
    if area_id is not None:
        stmt = stmt.where(HealthFacility.area_id == area_id)
    return list(db.scalars(stmt))


@router.get("/facilities/nearby", response_model=list[FacilityNearby])
def nearby_facilities(
    db: DbSession,
    _: CurrentUser,
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    radius_m: int = Query(5000, gt=0, le=50000),
    limit: int = Query(10, le=50),
) -> list[FacilityNearby]:
    """Health facilities within radius_m metres, nearest first."""
    origin = cast(LatLng(latitude=latitude, longitude=longitude).to_geometry(), Geography)
    distance = func.ST_Distance(cast(HealthFacility.location, Geography), origin)
    stmt = (
        select(HealthFacility, distance.label("distance"))
        .where(func.ST_DWithin(cast(HealthFacility.location, Geography), origin, radius_m))
        .order_by(distance)
        .limit(limit)
    )
    return [
        FacilityNearby.model_validate(
            {**FacilityRead.model_validate(f).model_dump(), "distance_m": round(d, 1)}
        )
        for f, d in db.execute(stmt)
    ]


@router.get("/infrastructure", response_model=list[InfrastructureRead])
def list_infrastructure(
    db: DbSession,
    _: CurrentUser,
    asset_type: InfrastructureType | None = None,
    area_id: int | None = None,
) -> list[InfrastructureAsset]:
    stmt = select(InfrastructureAsset).order_by(InfrastructureAsset.name)
    if asset_type:
        stmt = stmt.where(InfrastructureAsset.asset_type == asset_type)
    if area_id is not None:
        stmt = stmt.where(InfrastructureAsset.area_id == area_id)
    return list(db.scalars(stmt))
