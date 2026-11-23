from typing import Annotated, Any

from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import from_shape, to_shape
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from shapely.geometry import Point


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LatLng(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    def to_geometry(self) -> WKBElement:
        return from_shape(Point(self.longitude, self.latitude), srid=4326)


def _geometry_to_latlng(value: Any) -> Any:
    if isinstance(value, WKBElement):
        point = to_shape(value)
        return {"latitude": point.y, "longitude": point.x}
    return value


# Use as a field type on response schemas built from ORM objects with a POINT column.
PointField = Annotated[LatLng | None, BeforeValidator(_geometry_to_latlng)]


class Message(BaseModel):
    detail: str
