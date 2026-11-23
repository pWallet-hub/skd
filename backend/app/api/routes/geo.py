from fastapi import APIRouter, Query, Request, status
from geoalchemy2 import Geography
from sqlalchemy import cast, func, select

from app.api.deps import AdminUser, CurrentUser, DbSession, get_or_404
from app.models import AdministrativeArea, HealthFacility, InfrastructureAsset, School
from app.models.enums import AreaLevel, FacilityType, InfrastructureType
from app.schemas.common import LatLng
from app.schemas.geo import (
    AreaRead,
    FacilityNearby,
    FacilityRead,
    FacilityUpdate,
    FacilityWrite,
    InfrastructureRead,
    InfrastructureUpdate,
    InfrastructureWrite,
    SchoolRead,
    SchoolUpdate,
    SchoolWrite,
)
from app.services import audit

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


# ---- administration: create / update / delete reference places -------------
PLACES: dict[str, tuple[type, type, type, type, str]] = {
    "schools": (School, SchoolWrite, SchoolUpdate, SchoolRead, "school"),
    "facilities": (HealthFacility, FacilityWrite, FacilityUpdate, FacilityRead, "facility"),
    "infrastructure": (
        InfrastructureAsset,
        InfrastructureWrite,
        InfrastructureUpdate,
        InfrastructureRead,
        "infrastructure",
    ),
}


def _apply(obj, data: dict) -> None:
    location = data.pop("location", ...)
    if location is not ...:
        obj.location = LatLng(**location).to_geometry() if location else None
    for field, value in data.items():
        setattr(obj, field, value)


def _register_place_admin(path: str) -> None:
    model, write_schema, update_schema, read_schema, entity = PLACES[path]

    @router.post(
        f"/{path}",
        response_model=read_schema,
        status_code=status.HTTP_201_CREATED,
        name=f"create_{entity}",
    )
    def create(payload: write_schema, admin: AdminUser, db: DbSession, request: Request):  # type: ignore[valid-type]
        obj = model()
        _apply(obj, payload.model_dump())
        db.add(obj)
        db.flush()
        audit.record(
            db,
            admin,
            f"{entity}.create",
            entity,
            obj.id,
            f"Created {entity} {obj.name}",
            request=request,
        )
        db.commit()
        db.refresh(obj)
        return obj

    @router.patch(f"/{path}/{{obj_id}}", response_model=read_schema, name=f"update_{entity}")
    def update(
        obj_id: int, payload: update_schema, admin: AdminUser, db: DbSession, request: Request
    ):  # type: ignore[valid-type]
        obj = get_or_404(db, model, obj_id)
        _apply(obj, payload.model_dump(exclude_unset=True))
        audit.record(
            db,
            admin,
            f"{entity}.update",
            entity,
            obj.id,
            f"Updated {entity} {obj.name}",
            request=request,
        )
        db.commit()
        db.refresh(obj)
        return obj

    @router.delete(
        f"/{path}/{{obj_id}}", status_code=status.HTTP_204_NO_CONTENT, name=f"delete_{entity}"
    )
    def delete(obj_id: int, admin: AdminUser, db: DbSession, request: Request) -> None:
        obj = get_or_404(db, model, obj_id)
        audit.record(
            db,
            admin,
            f"{entity}.delete",
            entity,
            obj.id,
            f"Deleted {entity} {obj.name}",
            request=request,
        )
        db.delete(obj)
        db.commit()


for _path in PLACES:
    _register_place_admin(_path)
