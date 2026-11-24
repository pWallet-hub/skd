"""Child health card: a QR code the parent shows at a clinic (like digital vaccination cards).

The QR encodes a link with a short-lived signed token. Anyone holding the link can view a
minimal read-only summary until it expires — so links are time-limited and parent-initiated.
"""

from datetime import UTC, datetime

import jwt
from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, get_or_404
from app.api.routes.children import get_owned_child
from app.core.config import settings
from app.core.security import create_share_token, decode_share_token
from app.models import Child, SymptomReport
from app.schemas.share import HealthCard, HealthCardVaccine, ShareLink, ShareRequest
from app.services import audit
from app.services.child_health import immunization_schedule
from app.services.children import age_in_months

router = APIRouter(tags=["health card"])


@router.post("/children/{child_id}/share", response_model=ShareLink)
def create_share_link(
    child_id: int, payload: ShareRequest, user: CurrentUser, db: DbSession, request: Request
) -> ShareLink:
    child = get_owned_child(db, user, child_id)
    token, expires = create_share_token(child.id, payload.hours)
    audit.record(
        db, user, "child.share", "child", child.id,
        f"Health card shared for {payload.hours} h", request=request,
    )  # fmt: skip
    db.commit()
    url = f"{settings.public_base_url.rstrip('/')}/card/{token}"
    return ShareLink(token=token, url=url, expires_at=expires)


@router.get("/health-card/{token}", response_model=HealthCard)
def read_health_card(token: str, db: DbSession) -> HealthCard:
    """Public (no login): the token itself is the permission."""
    try:
        child_id = decode_share_token(token)
        expires = datetime.fromtimestamp(
            jwt.decode(token, options={"verify_signature": False})["exp"], UTC
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_410_GONE, "This health card link has expired") from None
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invalid health card link") from None
    child = get_or_404(db, Child, child_id)
    latest = child.measurements[-1] if child.measurements else None
    recent = db.scalars(
        select(SymptomReport)
        .where(SymptomReport.child_id == child.id)
        .order_by(SymptomReport.onset_date.desc())
        .limit(5)
    )
    return HealthCard(
        display_name=child.display_name,
        age_months=age_in_months(child.date_of_birth),
        date_of_birth=child.date_of_birth,
        sex=child.sex,
        latest_height_cm=float(latest.height_cm) if latest and latest.height_cm else None,
        latest_weight_kg=float(latest.weight_kg) if latest and latest.weight_kg else None,
        measured_on=latest.measured_on if latest else None,
        vaccines=[
            HealthCardVaccine(**{k: v[k] for k in ("name", "status", "given_on", "due_date")})
            for v in immunization_schedule(db, child)
        ],  # fmt: skip
        recent_concerns=[
            f"{r.onset_date:%d %b %Y}: {', '.join(s.name for s in r.symptoms)}"
            + (" (ongoing)" if r.is_ongoing else "")
            for r in recent
        ],
        health_notes=child.health_notes,
        expires_at=expires,
    )
