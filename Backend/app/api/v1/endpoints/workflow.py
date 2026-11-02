from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ....database import get_db
from ....core.permissions import journalist_or_editor
from ....core.errors import NotFoundError
from ....models import Utilisateur
from ....repositories import SignalRepository, DraftRepository
from ....schemas import ArticlePublicRead, CrossCheckRead, PublishRequest
from ....services.signals import cross_check_signal
from ....services.editorial import publish_draft
from ....workers.ingestion import process_pending_signals

router = APIRouter(prefix="/workflow", tags=["Workflow éditorial"])


@router.post("/process-pending")
def process_pending(db: Session = Depends(get_db), _: Utilisateur = Depends(journalist_or_editor)):
    return {"processed": process_pending_signals(db)}


@router.post("/signals/{signal_id}/cross-check", response_model=CrossCheckRead)
def cross_check(signal_id: int, db: Session = Depends(get_db),
                _: Utilisateur = Depends(journalist_or_editor)):
    signal = SignalRepository(db).get(signal_id)
    if signal is None:
        raise NotFoundError("Signal introuvable.")
    sources = cross_check_signal(db, signal)
    score = round(sum(item["concorde"] for item in sources) / len(sources) * 100, 2) if sources else 0
    return {"signal_id": signal_id, "sources": sources, "score_concordance": score}


@router.post("/drafts/{draft_id}/publish", response_model=ArticlePublicRead)
def publish(draft_id: int, payload: PublishRequest, db: Session = Depends(get_db),
            user: Utilisateur = Depends(journalist_or_editor)):
    draft = DraftRepository(db).get(draft_id)
    if draft is None:
        raise NotFoundError("Brouillon introuvable.")
    return publish_draft(db, draft, user, payload)
