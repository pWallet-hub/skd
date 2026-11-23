"""Audit trail helper. Call `record(...)` inside the same transaction as the change it describes."""

from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.models import AuditLog, User


def client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45]
    return request.client.host if request.client else None


def record(
    db: Session,
    actor: User | None,
    action: str,
    entity_type: str,
    entity_id: int | str | None = None,
    summary: str = "",
    details: dict[str, Any] | None = None,
    request: Request | None = None,
) -> AuditLog:
    """Stage an audit entry. The caller's commit persists it with the change itself."""
    entry = AuditLog(
        actor_id=actor.id if actor else None,
        actor_email=actor.email if actor else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        summary=summary[:255],
        details=details or {},
        ip_address=client_ip(request),
    )
    db.add(entry)
    return entry
