"""Persist a guided media analysis; no automated forensic result is invented."""
from ..database import SessionLocal
from ..core.rbac import authorize, Permission as P
from ..core.errors import ForbiddenError
from ..repositories.identity import UserRepository
from ..schemas.maharavo import MediaAnalysisRequest
from ..services.maharavo import record_media_analysis


def run(user_id: int, payload: MediaAnalysisRequest):
    with SessionLocal() as db:
        user = UserRepository(db).get_for_auth(user_id)
        if user is None or not user.actif:
            raise ForbiddenError("Droits insuffisants.")
        authorize(user,P.ANALYSIS_WRITE)
        return record_media_analysis(db, user, payload)
