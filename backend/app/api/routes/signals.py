from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, HealthTeamUser, InsightUser, get_or_404
from app.models import HealthSignal, InvestigationNote
from app.models.enums import SignalStatus
from app.schemas.surveillance import (
    DetectionResult,
    InvestigationNoteRead,
    NoteCreate,
    SignalDetail,
    SignalRead,
    SignalTransition,
)
from app.services.surveillance import can_transition, detect_signals

router = APIRouter(prefix="/signals", tags=["community signals"])


@router.get("", response_model=list[SignalRead])
def list_signals(
    db: DbSession, _: InsightUser, status_filter: SignalStatus | None = None
) -> list[HealthSignal]:
    stmt = select(HealthSignal).order_by(HealthSignal.score.desc(), HealthSignal.id.desc())
    if status_filter:
        stmt = stmt.where(HealthSignal.status == status_filter)
    return list(db.scalars(stmt))


@router.post("/detect", response_model=DetectionResult)
def run_detection(db: DbSession, _: HealthTeamUser) -> DetectionResult:
    """Run detection now (it also runs automatically every hour via Celery beat)."""
    created, updated = detect_signals(db)
    return DetectionResult(created=created, updated=updated)


@router.get("/{signal_id}", response_model=SignalDetail)
def get_signal(signal_id: int, db: DbSession, _: InsightUser) -> HealthSignal:
    return get_or_404(db, HealthSignal, signal_id)


@router.post("/{signal_id}/transition", response_model=SignalDetail)
def transition_signal(
    signal_id: int, payload: SignalTransition, user: HealthTeamUser, db: DbSession
) -> HealthSignal:
    """Move a signal through review. Every change requires a note (audit trail)."""
    signal = get_or_404(db, HealthSignal, signal_id)
    if not can_transition(signal.status, payload.status):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cannot move a signal from '{signal.status}' to '{payload.status}'",
        )
    db.add(
        InvestigationNote(
            signal_id=signal.id,
            author_id=user.id,
            body=payload.note,
            status_change=f"{signal.status}->{payload.status}",
        )
    )
    signal.status = payload.status
    if payload.status == SignalStatus.UNDER_REVIEW and signal.assigned_to_id is None:
        signal.assigned_to_id = user.id
    if payload.findings is not None:
        signal.findings = payload.findings
    db.commit()
    db.refresh(signal)
    return signal


@router.post(
    "/{signal_id}/notes", response_model=InvestigationNoteRead, status_code=status.HTTP_201_CREATED
)
def add_note(
    signal_id: int, payload: NoteCreate, user: HealthTeamUser, db: DbSession
) -> InvestigationNote:
    signal = get_or_404(db, HealthSignal, signal_id)
    note = InvestigationNote(signal_id=signal.id, author_id=user.id, body=payload.body)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note
