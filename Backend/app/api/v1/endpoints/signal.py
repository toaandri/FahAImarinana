from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....database import get_db
from ....core.permissions import journalist_or_editor
from ....models import SignalBrut, Utilisateur
from ....schemas import AnalyzeRequest, DraftRead, SignalIngest, SignalRead
from ....services import create_draft, cross_check_signal, ingest_signal

router = APIRouter(prefix="/signals", tags=["Veille et analyse"])


@router.post("/ingest", response_model=SignalRead, status_code=status.HTTP_201_CREATED)
def ingest(
    payload: SignalIngest,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(journalist_or_editor),
):
    try:
        signal = ingest_signal(db, payload)
        return signal
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{signal_id}/analyze",
    response_model=DraftRead,
    status_code=status.HTTP_201_CREATED,
)
def analyze(
    signal_id: int,
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(journalist_or_editor),
):
    signal = db.get(SignalBrut, signal_id)
    if signal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signal introuvable.")
    sources = [source.model_dump(mode="json") for source in payload.sources_croisees]
    if not sources:
        sources = cross_check_signal(db, signal)
    return create_draft(db, signal, sources)
