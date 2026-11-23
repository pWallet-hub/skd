"""Runtime-tunable settings. Environment variables are the defaults; admins can override them."""

from typing import Any

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import SystemSetting, User


class DetectionSettings(BaseModel):
    signal_window_days: int = Field(ge=1, le=60)
    signal_baseline_days: int = Field(ge=7, le=365)
    signal_min_reports: int = Field(ge=2, le=100)
    signal_ratio_threshold: float = Field(ge=1.0, le=20.0)
    aggregate_min_cell_size: int = Field(ge=1, le=50)

    @model_validator(mode="after")
    def baseline_longer_than_window(self) -> "DetectionSettings":
        if self.signal_baseline_days < self.signal_window_days:
            raise ValueError("Baseline period must be at least as long as the detection window")
        return self


TUNABLE_KEYS = tuple(DetectionSettings.model_fields)


def defaults() -> DetectionSettings:
    return DetectionSettings(**{k: getattr(settings, k) for k in TUNABLE_KEYS})


def get_detection_settings(db: Session) -> DetectionSettings:
    values: dict[str, Any] = defaults().model_dump()
    for row in db.scalars(select(SystemSetting).where(SystemSetting.key.in_(TUNABLE_KEYS))):
        values[row.key] = row.value
    return DetectionSettings(**values)


def save_detection_settings(db: Session, new: DetectionSettings, actor: User) -> dict[str, Any]:
    """Persist changed values; returns {key: [old, new]} for the audit log. Caller commits."""
    current = get_detection_settings(db)
    changes: dict[str, Any] = {}
    for key in TUNABLE_KEYS:
        old_value, new_value = getattr(current, key), getattr(new, key)
        if old_value == new_value:
            continue
        changes[key] = [old_value, new_value]
        row = db.get(SystemSetting, key)
        if row is None:
            db.add(SystemSetting(key=key, value=new_value, updated_by_id=actor.id))
        else:
            row.value = new_value
            row.updated_by_id = actor.id
    return changes
