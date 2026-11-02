"""Persist private Gemini observations without any publication capability."""
import base64
import hashlib
from threading import BoundedSemaphore
from sqlalchemy import select
from ..core.errors import ConflictError, DomainError, NotFoundError, IntegrationUnavailableError
from ..core.rbac import Permission as P, authorize
from ..core.security import now
from ..core.config import get_settings
from ..database.scope import scope_for_user
from ..models import MediaAnalysis
from ..schemas.vision import REVIEW_NOTICE
from ..integrations.ai.gemini import analyze_video_clip, GeminiUnavailableError

_slots = BoundedSemaphore(2)


class VisionBusyError(DomainError):
    status_code = 429


def analyze_clip(db, user, clip):
    authorize(user, P.ANALYSIS_WRITE)
    scope_for_user(db, user)
    if clip.case_id is not None:
        from .investigations import get_case
        get_case(db, clip.case_id, writable=True)
    key = f'{clip.capture_id}:{clip.sequence}'
    digest = hashlib.sha256(base64.b64decode(clip.video_base64)).hexdigest()
    existing = db.scalar(select(MediaAnalysis).where(MediaAnalysis.utilisateur_id == user.id,
                                                     MediaAnalysis.capture_key == key))
    if existing:
        if existing.empreinte_sha256 != digest or existing.case_id != clip.case_id:
            raise ConflictError('Cet identifiant de clip correspond à un autre contenu ou dossier.')
        if existing.status == 'completed':
            return existing
        raise ConflictError('Ce clip a déjà été soumis. Consultez son état ; aucune nouvelle facturation automatique.')
    if not get_settings().gemini_api_key.get_secret_value().strip():
        raise IntegrationUnavailableError('GEMINI_API_KEY doit être configurée sur le backend.')
    if not _slots.acquire(blocking=False):
        raise VisionBusyError('Analyse vidéo occupée ; réessayez après la fin des traitements en cours.')
    record = None
    try:
        metadata = {
            'version': 1, 'provider': 'gemini', 'model': get_settings().gemini_vision_model,
            'capture_id': str(clip.capture_id), 'sequence': clip.sequence,
            'captured_at': clip.captured_at.isoformat(), 'received_at': now().isoformat(),
            'duration_seconds': clip.duration_seconds, 'language': clip.language,
            'review_notice': REVIEW_NOTICE,
        }
        record = MediaAnalysis(utilisateur_id=user.id, case_id=clip.case_id, type_media='video',
            reference_originale='capture://' + key, empreinte_sha256=digest,
            outil='gemini-vision', version_outil=get_settings().gemini_vision_model,
            observations=[], limites=[REVIEW_NOTICE], indice_indicatif='non_evalue',
            cree_le=now(), status='running', capture_key=key, result=metadata)
        db.add(record); db.commit()
        try:
            analysis = analyze_video_clip(clip)
        except GeminiUnavailableError as exc:
            record.status = 'failed'
            record.result = {**metadata, 'finished_at': now().isoformat(),
                             'error': {'code': exc.code, 'message': str(exc)}}
            db.commit()
            error = IntegrationUnavailableError(str(exc))
            error.status_code = exc.http_status
            raise error from None
        except Exception:
            record.status = 'failed'
            record.result = {**metadata, 'finished_at': now().isoformat(),
                             'error': {'code': 'analysis_failed', 'message': 'Analyse vidéo interrompue.'}}
            db.commit()
            raise IntegrationUnavailableError('Analyse vidéo interrompue.') from None
        record.observations = [f'{item.time_seconds:.2f}s : {item.description}' for item in analysis.observations]
        record.limites = [REVIEW_NOTICE, *analysis.limitations]
        record.result = {**metadata, 'finished_at': now().isoformat(), 'analysis': analysis.model_dump()}
        record.status = 'completed'
        db.commit()
        return record
    finally:
        _slots.release()


def own_analysis(db, user, identifier):
    authorize(user, P.ANALYSIS_WRITE)
    scope_for_user(db, user)
    record = db.scalar(select(MediaAnalysis).where(MediaAnalysis.id == identifier,
        MediaAnalysis.utilisateur_id == user.id, MediaAnalysis.outil == 'gemini-vision'))
    if record is None:
        raise NotFoundError('Analyse vidéo introuvable.')
    return record
