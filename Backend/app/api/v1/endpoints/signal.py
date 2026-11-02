from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from ....database import get_db
from ....core.permissions import journalist_or_editor
from ....core.errors import NotFoundError
from ....models import Utilisateur
from ....schemas import AnalyzeRequest, DraftRead, SignalIngest, SignalRead
from ....repositories import SignalRepository
from ....services.signals import ingest_signal, cross_check_signal
from ....services.drafts import create_draft

router = APIRouter(prefix="/signals", tags=["Veille et analyse"])


@router.post("/ingest", response_model=SignalRead, status_code=status.HTTP_201_CREATED)
def ingest(payload: SignalIngest, db: Session = Depends(get_db),
           _: Utilisateur = Depends(journalist_or_editor)):
    return ingest_signal(db, payload)


@router.post("/{signal_id}/analyze", response_model=DraftRead, status_code=status.HTTP_201_CREATED)
def analyze(signal_id: int, payload: AnalyzeRequest, db: Session = Depends(get_db),
            _: Utilisateur = Depends(journalist_or_editor)):
    signal = SignalRepository(db).get(signal_id)
    if signal is None:
        raise NotFoundError("Signal introuvable.")
    sources = [source.model_dump(mode="json") for source in payload.sources_croisees]
    return create_draft(db, signal, sources or cross_check_signal(db, signal))
