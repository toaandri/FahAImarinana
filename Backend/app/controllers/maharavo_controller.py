from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import journalist_or_editor
from ..maharavo_service import record_confidence, record_media_analysis, run_research
from ..models import Utilisateur
from ..schemas import (
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
):
    return run_research(
        db, user, payload.sujet, payload.questions, payload.periode,
        payload.langues, payload.territoire,
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
    try:
        return record_confidence(db, user, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
