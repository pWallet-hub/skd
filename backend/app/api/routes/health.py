from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession

router = APIRouter(tags=["system"])


@router.get("/health")
def health(db: DbSession) -> dict[str, str]:
    """Liveness/readiness probe used by Docker healthchecks."""
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
