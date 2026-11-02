from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ....database import get_db
from ....core.permissions import journalist_or_editor
from ....services.maharavo import record_confidence, record_media_analysis, run_research
from ....models import Utilisateur
from ....integrations.maharavo.research import ResearchProvider, get_research_provider
from ....schemas import (
    ConfidenceRead,
    ConfidenceRequest,
    MaharavoResearchRead,
    MaharavoResearchRequest,
    MediaAnalysisRead,
    MediaAnalysisRequest,
)

router = APIRouter(prefix="/maharavo", tags=["Maharavo IA"])


@router.post("/research", response_model=MaharavoResearchRead, status_code=status.HTTP_201_CREATED)
def research(
    payload: MaharavoResearchRequest,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(journalist_or_editor),
    provider: ResearchProvider = Depends(get_research_provider),
):
    return run_research(
        db, user, payload.sujet, payload.questions, payload.periode,
        payload.langues, payload.territoire, provider=provider,
    )


@router.post("/media-analysis", response_model=MediaAnalysisRead, status_code=status.HTTP_201_CREATED)
def media_analysis(
    payload: MediaAnalysisRequest,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(journalist_or_editor),
):
    return record_media_analysis(db, user, payload)


@router.post("/confidence", response_model=ConfidenceRead, status_code=status.HTTP_201_CREATED)
def confidence(
    payload: ConfidenceRequest,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(journalist_or_editor),
):
    return record_confidence(db, user, payload)
