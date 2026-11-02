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
from .research import build_research_answer

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
def create_chat_session(db: Session, user: Utilisateur, titre: str) -> SessionChat:
    now = datetime.now(timezone.utc)
    session = SessionChat(
        utilisateur_id=user.id,
        titre=titre,
        cree_le=now,
        mise_a_jour_le=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_chat_sessions(db: Session, user: Utilisateur) -> list[SessionChat]:
    return list(
        db.scalars(
            select(SessionChat)
            .where(SessionChat.utilisateur_id == user.id)
            .order_by(SessionChat.mise_a_jour_le.desc())
        )
    )


def get_chat_messages(db: Session, session_id: int, user: Utilisateur) -> list[MessageChat]:
    session = db.get(SessionChat, session_id)
    if session is None or session.utilisateur_id != user.id:
        raise ValueError("Session introuvable.")
    return list(
        db.scalars(
            select(MessageChat)
            .where(MessageChat.session_id == session_id)
            .order_by(MessageChat.horodatage.asc())
        )
    )


def ask_copilot(db: Session, user: Utilisateur, session_id: int, question: str) -> tuple[MessageChat, MessageChat, list[dict], list[dict]]:
    session = db.get(SessionChat, session_id)
    if session is None or session.utilisateur_id != user.id:
        raise ValueError("Session introuvable.")
    now = datetime.now(timezone.utc)
    user_message = MessageChat(
        session_id=session.id,
        role="journaliste",
        contenu=question,
        citations=[],
        horodatage=now,
    )
    db.add(user_message)
    answer, citations, chronology = build_research_answer(db, question)
    assistant_message = MessageChat(
        session_id=session.id,
        role="assistant",
        contenu=answer,
        citations=citations,
        horodatage=datetime.now(timezone.utc),
    )
    db.add(assistant_message)
    session.mise_a_jour_le = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    return user_message, assistant_message, citations, chronology
