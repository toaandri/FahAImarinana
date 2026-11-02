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
from .research import index_certified_article

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
def publish_draft(
    db: Session,
    draft: DraftIA,
    user: Utilisateur,
    payload,
) -> ArticleCertifie:
    if user.role not in {"Journaliste", "Editeur"}:
        raise ValueError("Seuls les journalistes et éditeurs peuvent publier.")
    if draft.statut == "En_Cours":
        raise ValueError("Ce brouillon a déjà été publié ou est en cours de publication.")
    article = ArticleCertifie(
        draft_id=draft.id,
        titre_final=payload.titre_final,
        corps_article=payload.corps_article,
        categorie=payload.categorie,
        statut_verification=payload.statut_verification,
        id_journaliste_validateur=user.id,
        horodatage_validation=datetime.now(timezone.utc),
        contenu_optimise_sms=payload.contenu_optimise_sms,
    )
    draft.statut = "En_Cours"
    db.add(article)
    db.commit()
    db.refresh(article)
    index_certified_article(db, article)
    return article
