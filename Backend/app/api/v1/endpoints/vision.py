from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ....core.config import get_settings
from ....core.permissions import require_permission
from ....core.rbac import Permission as P
from ....database import get_db
from ....models import User, MediaAnalysis
from ....schemas.vision import VideoClipRequest, VideoAnalysisRead, MAX_VIDEO_BYTES
from ....services.vision import analyze_clip, own_analysis

router = APIRouter(prefix='/vision', tags=['Gemini Vision — vidéo privée'])


@router.get('/status')
def capabilities(user: User = Depends(require_permission(P.ANALYSIS_WRITE))):
    settings = get_settings()
    return {'configured': bool(settings.gemini_api_key.get_secret_value().strip()),
            'capture_id': str(uuid4()),
            'provider': 'gemini', 'model': settings.gemini_vision_model,
            'clip_seconds': 6, 'max_video_bytes': MAX_VIDEO_BYTES,
            'max_duration_seconds': 10, 'requires_human_review': True}


@router.post('/video', response_model=VideoAnalysisRead, status_code=201,
             responses={413: {'description': 'Clip trop volumineux.'},
                        503: {'description': 'Gemini absent, indisponible ou requête refusée.'},
                        504: {'description': 'Délai Gemini dépassé.'}})
def video(payload: VideoClipRequest, db: Session = Depends(get_db),
          user: User = Depends(require_permission(P.ANALYSIS_WRITE))):
    return analyze_clip(db, user, payload)


@router.get('/analyses/{analysis_id}', response_model=VideoAnalysisRead)
def analysis(analysis_id: int, db: Session = Depends(get_db),
             user: User = Depends(require_permission(P.ANALYSIS_WRITE))):
    return own_analysis(db, user, analysis_id)


@router.get('/analyses', response_model=list[VideoAnalysisRead])
def analyses(capture_id: UUID, db: Session = Depends(get_db),
             user: User = Depends(require_permission(P.ANALYSIS_WRITE)),
             limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)):
    return list(db.scalars(select(MediaAnalysis).where(MediaAnalysis.utilisateur_id == user.id,
        MediaAnalysis.outil == 'gemini-vision', MediaAnalysis.capture_key.startswith(str(capture_id) + ':'))
        .order_by(MediaAnalysis.id).limit(limit).offset(offset)))
