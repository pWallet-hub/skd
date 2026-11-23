from fastapi import APIRouter, HTTPException, UploadFile, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, ParentUser, get_or_404
from app.core.storage import ALLOWED_IMAGE_TYPES, delete_file, upload_file
from app.models import Child, GrowthMeasurement, User
from app.models.enums import UserRole
from app.schemas.family import (
    ChildCreate,
    ChildRead,
    ChildUpdate,
    MeasurementCreate,
    MeasurementRead,
)
from app.services.children import to_child_read

router = APIRouter(prefix="/children", tags=["children"])

MAX_PHOTO_BYTES = 5 * 1024 * 1024


def get_owned_child(db: DbSession, user: User, child_id: int) -> Child:
    """Parents can only see their own children. Admins can see any child."""
    child = get_or_404(db, Child, child_id)
    if child.guardian_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Child not found")
    return child


@router.get("", response_model=list[ChildRead])
def list_children(user: ParentUser, db: DbSession) -> list[ChildRead]:
    children = db.scalars(
        select(Child).where(Child.guardian_id == user.id).order_by(Child.date_of_birth)
    )
    return [to_child_read(c) for c in children]


@router.post("", response_model=ChildRead, status_code=status.HTTP_201_CREATED)
def create_child(payload: ChildCreate, user: ParentUser, db: DbSession) -> ChildRead:
    child = Child(guardian_id=user.id, **payload.model_dump())
    db.add(child)
    db.commit()
    db.refresh(child)
    return to_child_read(child)


@router.get("/{child_id}", response_model=ChildRead)
def get_child(child_id: int, user: CurrentUser, db: DbSession) -> ChildRead:
    return to_child_read(get_owned_child(db, user, child_id))


@router.patch("/{child_id}", response_model=ChildRead)
def update_child(
    child_id: int, payload: ChildUpdate, user: CurrentUser, db: DbSession
) -> ChildRead:
    child = get_owned_child(db, user, child_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(child, field, value)
    db.commit()
    db.refresh(child)
    return to_child_read(child)


@router.delete("/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_child(child_id: int, user: CurrentUser, db: DbSession) -> None:
    child = get_owned_child(db, user, child_id)
    if child.photo_key:
        delete_file(child.photo_key, "private")
    db.delete(child)
    db.commit()


@router.put("/{child_id}/photo", response_model=ChildRead)
def upload_child_photo(
    child_id: int, file: UploadFile, user: CurrentUser, db: DbSession
) -> ChildRead:
    """Stored in the PRIVATE SeaweedFS bucket; returned only as a short-lived signed URL."""
    child = get_owned_child(db, user, child_id)
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Unsupported image type")
    if file.size and file.size > MAX_PHOTO_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Image is larger than 5 MB")
    old_key = child.photo_key
    child.photo_key = upload_file(
        file.file,
        filename=file.filename or "photo",
        content_type=file.content_type,
        visibility="private",
        prefix=f"children/{child.id}",
    )
    db.commit()
    if old_key:
        delete_file(old_key, "private")
    return to_child_read(child)


@router.get("/{child_id}/measurements", response_model=list[MeasurementRead])
def list_measurements(child_id: int, user: CurrentUser, db: DbSession) -> list[GrowthMeasurement]:
    return get_owned_child(db, user, child_id).measurements


@router.post(
    "/{child_id}/measurements",
    response_model=MeasurementRead,
    status_code=status.HTTP_201_CREATED,
)
def add_measurement(
    child_id: int, payload: MeasurementCreate, user: CurrentUser, db: DbSession
) -> GrowthMeasurement:
    child = get_owned_child(db, user, child_id)
    measurement = GrowthMeasurement(child_id=child.id, **payload.model_dump())
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return measurement
