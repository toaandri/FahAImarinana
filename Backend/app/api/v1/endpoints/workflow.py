from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ....database import get_db
from ....core.permissions import require_permission
from ....core.rbac import Permission as P, authorize
from ....core.errors import NotFoundError
from ....models import Utilisateur
from ....repositories import SignalRepository, DraftRepository
from ....schemas import ArticlePublicRead, CrossCheckRead, PublishRequest
from ....services.signals import cross_check_signal
from ....services.editorial import publish_draft
from ....workers.ingestion import process_pending_signals

router = APIRouter(prefix="/workflow", tags=["Workflow éditorial"])


@router.post("/process-pending")
def process_pending(db: Session = Depends(get_db), _: Utilisateur = Depends(require_permission(P.TASKS_RUN))):
    authorize(_,P.DRAFT_CREATE)
    return {"processed": process_pending_signals(db)}


@router.post("/signals/{signal_id}/cross-check", response_model=CrossCheckRead)
def cross_check(signal_id: int, db: Session = Depends(get_db),
                _: Utilisateur = Depends(require_permission(P.RESEARCH_RUN))):
    signal = SignalRepository(db).get(signal_id)
    if signal is None:
        raise NotFoundError("Signal introuvable.")
    sources = cross_check_signal(db, signal)
    score = round(sum(item["concorde"] for item in sources) / len(sources) * 100, 2) if sources else 0
    return {"signal_id": signal_id, "sources": sources, "score_concordance": score}


@router.post("/drafts/{draft_id}/publish", response_model=ArticlePublicRead)
def publish(draft_id: int, payload: PublishRequest, db: Session = Depends(get_db),
            user: Utilisateur = Depends(require_permission(P.PUBLISH))):
    draft = DraftRepository(db).get(draft_id)
    if draft is None:
        raise NotFoundError("Brouillon introuvable.")
    return publish_draft(db, draft, user, payload)


from ....schemas.editorial import (ValidateDraftRequest,ReviewDraftRequest,DraftVersionRead,CorrectionRequest,WithdrawalRequest)
from ....services.draft_workflow import validate_draft,review_draft
from ....services.publications import correct_publication,withdraw_publication


@router.post('/drafts/{draft_id}/review',response_model=DraftVersionRead)
def review(draft_id: int,payload: ReviewDraftRequest,db: Session=Depends(get_db),
           user: Utilisateur=Depends(require_permission(P.DRAFT_REVIEW))):
    return review_draft(db,user,draft_id,payload)


@router.post('/drafts/{draft_id}/validate',response_model=DraftVersionRead)
def validate(draft_id: int,payload: ValidateDraftRequest,db: Session=Depends(get_db),
             user: Utilisateur=Depends(require_permission(P.VERSION_VALIDATE))):
    return validate_draft(db,user,draft_id,payload)


@router.post('/publications/{publication_id}/correct',response_model=ArticlePublicRead)
def correct(publication_id: int,payload: CorrectionRequest,db: Session=Depends(get_db),
            user: Utilisateur=Depends(require_permission(P.CORRECT))):
    return correct_publication(db,user,publication_id,payload,reason=payload.reason)


@router.post('/publications/{publication_id}/withdraw',response_model=ArticlePublicRead)
def withdraw(publication_id: int,payload: WithdrawalRequest,db: Session=Depends(get_db),
             user: Utilisateur=Depends(require_permission(P.CORRECT))):
    return withdraw_publication(db,user,publication_id,reason=payload.reason)
