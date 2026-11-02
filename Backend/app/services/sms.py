import logging
import re
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from sqlalchemy.orm import Session
from ..models import (ArticleCertifie, ContactJournaliste, DocumentRecherche, DraftIA,
                      HistoriqueSms, MessageChat, SessionChat, SignalBrut, SourceSurveillee, Utilisateur)
from ..core.config import get_settings
from ..core.errors import ConflictError, NotFoundError, ForbiddenError
from ..repositories import ArticleRepository, DraftRepository, SignalRepository, SourceRepository, ResearchRepository, ChatRepository, ContactRepository
from ..utils.text import normalize_text, tokenize as _tokenize
logger = logging.getLogger(__name__)

SENSITIVE_KEYWORDS = (
    "grève",
    "greve",
    "manifestation",
    "délestage",
    "delestage",
    "coupure",
    "électricité",
    "electricite",
    "eau",
    "politique",
)
SECURITY_RESPONSE = "Sujet en cours de vérification par nos journalistes"
def answer_citizen_sms(db: Session, payload) -> tuple[str, str]:
    query = normalize_text(payload.message)
    words = [word for word in query.casefold().split() if len(word) >= 4][:8]
    articles = db.scalars(
        select(ArticleCertifie).where(
            or_(*[ArticleCertifie.corps_article.ilike(f"%{word}%") for word in words])
        ).limit(1)
    ).all() if words else []
    if articles:
        response, status = articles[0].contenu_optimise_sms, "Trouve"
    else:
        response, status = SECURITY_RESPONSE, "Non_Trouve"
    db.add(HistoriqueSms(
        numero_expediteur=payload.numero_expediteur,
        message_recu=payload.message,
        message_envoye=response,
        horodatage=datetime.now(timezone.utc),
        statut_reponse=status,
    ))
    db.commit()
    return response, status
