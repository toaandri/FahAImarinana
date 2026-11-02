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
def alert_journalists(db: Session, signal: SignalBrut, send_sms) -> list[str]:
    if not signal.est_urgent:
        return []
    contacts = db.scalars(
        select(ContactJournaliste).where(ContactJournaliste.alertes_actives.is_(True))
    ).all()
    short_id = sha256(f"signal:{signal.id}".encode()).hexdigest()[:8].upper()
    message = f"ALERTE {short_id}: {signal.contenu_normalise[:120]}"
    sent = []
    for contact in contacts:
        send_sms(contact.numero_telephone, message)
        sent.append(contact.numero_telephone)
    return sent
