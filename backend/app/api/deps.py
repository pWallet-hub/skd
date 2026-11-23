from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import User
from app.models.enums import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = int(decode_token(token, "access"))
    except (jwt.InvalidTokenError, ValueError):
        raise unauthorized from None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    """Dependency factory: allow only the given roles (admins are always allowed)."""
    allowed = set(roles) | {UserRole.ADMIN}

    def checker(user: CurrentUser) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "You do not have access to this resource"
            )
        return user

    return checker


# Role groups, named after what they protect
HEALTH_TEAM = (UserRole.HEALTH_REVIEWER, UserRole.ANALYST)
INSIGHT_VIEWERS = (UserRole.HEALTH_REVIEWER, UserRole.ANALYST, UserRole.INSTITUTION)

HealthTeamUser = Annotated[User, Depends(require_roles(*HEALTH_TEAM))]
InsightUser = Annotated[User, Depends(require_roles(*INSIGHT_VIEWERS))]
ReviewerUser = Annotated[User, Depends(require_roles(UserRole.HEALTH_REVIEWER))]
ParentUser = Annotated[User, Depends(require_roles(UserRole.PARENT))]
AdminUser = Annotated[User, Depends(require_roles())]


def get_or_404[T](db: Session, model: type[T], obj_id: int) -> T:
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{model.__name__} not found")
    return obj
