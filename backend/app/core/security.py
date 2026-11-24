from datetime import UTC, datetime, timedelta
from typing import Literal

import bcrypt
import jwt

from app.core.config import settings

ALGORITHM = "HS256"
TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=settings.bcrypt_rounds)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(subject: str | int, token_type: TokenType) -> str:
    if token_type == "access":
        expires = timedelta(minutes=settings.access_token_expire_minutes)
    else:
        expires = timedelta(days=settings.refresh_token_expire_days)
    now = datetime.now(UTC)
    payload = {"sub": str(subject), "type": token_type, "iat": now, "exp": now + expires}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str, expected_type: TokenType) -> str:
    """Return the token subject, or raise jwt.InvalidTokenError."""
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Wrong token type")
    return payload["sub"]


# ---- child health-card share links (QR codes) ---------------------------------
SHARE_TOKEN_TYPE = "child_share"


def create_share_token(child_id: int, hours: int) -> tuple[str, datetime]:
    """Short-lived, read-only token for one child's health card (shown as a QR code)."""
    expires = datetime.now(UTC) + timedelta(hours=hours)
    payload = {"sub": str(child_id), "type": SHARE_TOKEN_TYPE, "exp": expires}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM), expires


def decode_share_token(token: str) -> int:
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    if payload.get("type") != SHARE_TOKEN_TYPE:
        raise jwt.InvalidTokenError("Wrong token type")
    return int(payload["sub"])
