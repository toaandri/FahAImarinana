from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import journalist_or_editor
from ..models import DraftIA, SignalBrut, Utilisateur
from ..schemas import ArticlePublicRead, CrossCheckRead, PublishRequest
from ..services import cross_check_signal, publish_draft

router = APIRouter(prefix="/workflow", tags=["Workflow éditorial"])


@router.post("/signals/{signal_id}/cross-check", response_model=CrossCheckRead)
def cross_check(signal_id: int, db: Session = Depends(get_db)):
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
