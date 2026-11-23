from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole
from app.schemas.common import ORMModel


class UserRead(ORMModel):
    id: int
    email: EmailStr
    full_name: str
    phone_number: str | None
    role: UserRole
    preferred_language: str
    home_area_id: int | None
    created_at: datetime


class ParentRegister(BaseModel):
    """Self-registration is only available for parents/guardians."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=150)
    phone_number: str | None = Field(default=None, max_length=32)
    home_area_id: int | None = None
    preferred_language: str = "en"


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone_number: str | None = Field(default=None, max_length=32)
    home_area_id: int | None = None
    preferred_language: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
