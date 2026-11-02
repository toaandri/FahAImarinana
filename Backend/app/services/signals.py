from ..core.constants import SENSITIVE_KEYWORDS
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from ..models import SignalBrut
from ..core.errors import NotFoundError
from ..repositories import ArticleRepository, SignalRepository, SourceRepository
from ..utils.text import normalize_text, tokenize as _tokenize
logger = logging.getLogger(__name__)

def ingest_signal(db: Session, payload) -> SignalBrut:
    source = SourceRepository(db).get(payload.source_id)
    if source is None or source.statut != "Actif":
        raise NotFoundError("La source est introuvable ou inactive.")

    normalized = normalize_text(payload.contenu)
    lowered = normalized.casefold()
    keywords = [word for word in SENSITIVE_KEYWORDS if word in lowered]
    since = payload.horodatage_publication - timedelta(minutes=30)
    recent_count = SignalRepository(db).count_between(since, payload.horodatage_publication)
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
    """Return research leads; lexical similarity cannot establish concordance."""
    terms = [term for term in _tokenize(signal.contenu_normalise) if len(term) > 4][:8]
    return [
        {"titre": article.titre_final,
         "url": f"https://internal.fanilo/articles-certifies/{article.id}",
         "extrait": article.corps_article[:500], "concorde": False, "officielle": False}
        for article in ArticleRepository(db).matching(terms, 20)
    ]
