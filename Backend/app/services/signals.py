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
def ingest_signal(db: Session, payload) -> SignalBrut:
    source = db.get(SourceSurveillee, payload.source_id)
    if source is None or source.statut != "Actif":
        raise ValueError("La source est introuvable ou inactive.")

    normalized = normalize_text(payload.contenu)
    lowered = normalized.casefold()
    keywords = [word for word in SENSITIVE_KEYWORDS if word in lowered]
    since = payload.horodatage_publication - timedelta(minutes=30)
    recent_count = db.scalar(
        select(func.count(SignalBrut.id)).where(
            SignalBrut.horodatage_publication >= since,
            SignalBrut.horodatage_publication <= payload.horodatage_publication,
        )
    ) or 0
    virality = min(100.0, float(payload.nombre_interactions) / 10 + recent_count * 5)

    signal = SignalBrut(
        source_id=payload.source_id,
        contenu_brut=payload.contenu,
        contenu_normalise=normalized,
        url_origine=str(payload.url_origine),
        horodatage_publication=payload.horodatage_publication,
        auteur=payload.auteur,
        nombre_interactions=payload.nombre_interactions,
        niveau_viralite=round(virality, 2),
        mots_cles_detectes=sorted(set(keywords)),
        est_urgent=bool(keywords and virality >= 50),
    )
    source.derniere_verification = datetime.now(timezone.utc)
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return signal


def cross_check_signal(db: Session, signal: SignalBrut) -> list[dict]:
    terms = [term for term in signal.contenu_normalise.casefold().split() if len(term) > 4][:8]
    if not terms:
        return []
    documents = db.scalars(
        select(ArticleCertifie).where(
            or_(*[ArticleCertifie.corps_article.ilike(f"%{term}%") for term in terms])
        ).limit(20)
    ).all()
    return [
        {
            "titre": article.titre_final,
            "url": f"https://internal.fanilo/articles-certifies/{article.id}",
            "extrait": article.corps_article[:500],
            "concorde": True,
            "officielle": True,
        }
        for article in documents
    ]
