from app.models.enums import AreaLevel, FacilityType, InfrastructureType
from app.schemas.common import ORMModel, PointField


class AreaRead(ORMModel):
    id: int
    code: str
    name: str
    level: AreaLevel
    parent_id: int | None
    centroid: PointField = None


class SchoolRead(ORMModel):
    id: int
    name: str
    area_id: int | None
    location: PointField = None
    is_verified: bool


class FacilityRead(ORMModel):
    id: int
    name: str
    facility_type: FacilityType
    area_id: int | None
    location: PointField = None
    phone_number: str | None
    opening_hours: str | None
    is_verified: bool


class FacilityNearby(FacilityRead):
    distance_m: float


class InfrastructureRead(ORMModel):
    id: int
    name: str
    asset_type: InfrastructureType
    area_id: int | None
    location: PointField = None
    data_source: str | None
    notes: str | None
