from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo

from app.models.enums import AreaLevel, FacilityType, InfrastructureType
from app.schemas.common import LatLng, ORMModel, PointField


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


# ---- write models (admin) ---------------------------------------------------
class _PlaceWrite(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    area_id: int | None = None
    location: LatLng | None = None


class SchoolWrite(_PlaceWrite):
    is_verified: bool = False


class FacilityWrite(_PlaceWrite):
    facility_type: FacilityType
    phone_number: str | None = Field(default=None, max_length=32)
    opening_hours: str | None = Field(default=None, max_length=120)
    is_verified: bool = False


class InfrastructureWrite(_PlaceWrite):
    asset_type: InfrastructureType
    data_source: str | None = Field(default=None, max_length=200)
    notes: str | None = None


def partial[M: BaseModel](model: type[M]) -> type[M]:
    """Same fields and validation as `model`, but every field optional (for PATCH)."""
    fields = {
        name: (info.annotation | None, FieldInfo.merge_field_infos(info, default=None))
        for name, info in model.model_fields.items()
    }
    return create_model(f"{model.__name__}Update", **fields)  # type: ignore[call-overload]


SchoolUpdate = partial(SchoolWrite)
FacilityUpdate = partial(FacilityWrite)
InfrastructureUpdate = partial(InfrastructureWrite)
