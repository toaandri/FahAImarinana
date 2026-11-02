from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....database import get_db
from ....core.permissions import journalist_or_editor
from ....models import DraftIA, SignalBrut, Utilisateur
from ....schemas import ArticlePublicRead, CrossCheckRead, PublishRequest
from ....services import cross_check_signal, publish_draft
from ....workers import process_pending_signals

router = APIRouter(prefix="/workflow", tags=["Workflow éditorial"])


@router.post("/process-pending", status_code=status.HTTP_200_OK)
def process_pending(
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(journalist_or_editor),
):
    """Run one supervised worker pass; scheduling remains an infrastructure concern."""
    return {"processed": process_pending_signals(db)}


@router.post("/signals/{signal_id}/cross-check", response_model=CrossCheckRead)
def cross_check(
    signal_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(journalist_or_editor),
):
    signal = db.get(SignalBrut, signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail="Signal introuvable.")
    sources = cross_check_signal(db, signal)
    score = round(sum(item["concorde"] for item in sources) / len(sources) * 100, 2) if sources else 0
    return {"signal_id": signal_id, "sources": sources, "score_concordance": score}


@router.post("/drafts/{draft_id}/publish", response_model=ArticlePublicRead)
def publish(
    draft_id: int,
    payload: PublishRequest,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(journalist_or_editor),
):
    draft = db.get(DraftIA, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Brouillon introuvable.")
    if draft.statut == "Rejete":
        raise HTTPException(status_code=409, detail="Un brouillon rejeté ne peut pas être publié.")
    try:
        return publish_draft(db, draft, user, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
