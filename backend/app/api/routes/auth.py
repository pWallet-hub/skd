from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.models import User
from app.models.enums import UserRole
from app.schemas.user import (
    LoginRequest,
    ParentRegister,
    RefreshRequest,
    TokenPair,
    UserRead,
    UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _tokens(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_token(user.id, "access"),
        refresh_token=create_token(user.id, "refresh"),
    )


def _authenticate(db: DbSession, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    return user


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_parent(payload: ParentRegister, db: DbSession) -> User:
    email = payload.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        home_area_id=payload.home_area_id,
        preferred_language=payload.preferred_language,
        role=UserRole.PARENT,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: DbSession) -> TokenPair:
    return _tokens(_authenticate(db, payload.email, payload.password))


@router.post("/token", response_model=TokenPair, include_in_schema=False)
def login_form(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession) -> TokenPair:
    """OAuth2 password flow, used by the 'Authorize' button in Swagger UI."""
    return _tokens(_authenticate(db, form.username, form.password))


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    try:
        user = db.get(User, int(decode_token(payload.refresh_token, "refresh")))
    except (jwt.InvalidTokenError, ValueError):
        user = None
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    return _tokens(user)


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser) -> User:
    return user


@router.patch("/me", response_model=UserRead)
def update_me(payload: UserUpdate, user: CurrentUser, db: DbSession) -> User:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
