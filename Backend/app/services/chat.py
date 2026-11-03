import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..database.scope import scope_for_user, set_scope
from ..models import MessageChat, SessionChat, Utilisateur
from ..core.errors import NotFoundError
from ..repositories import ChatRepository
logger = logging.getLogger(__name__)
from .research import build_research_answer
from ..utils.languages import resolve_language, Language

def create_chat_session(db: Session, user: Utilisateur, titre: str) -> SessionChat:
    scope_for_user(db, user)
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
    return ChatRepository(db).for_user(user.id)



def get_chat_messages(db: Session, session_id: int, user: Utilisateur) -> list[MessageChat]:
    session = ChatRepository(db).get(session_id)
    if session is None or session.utilisateur_id != user.id:
        raise NotFoundError("Session introuvable.")
    return ChatRepository(db).messages(session_id)



def ask_copilot(db: Session, user: Utilisateur, session_id: int, question: str, *, language: Language | None = None) -> tuple[MessageChat, MessageChat, list[dict], list[dict]]:
    session = ChatRepository(db).get(session_id)
    if session is None or session.utilisateur_id != user.id:
        raise NotFoundError("Session introuvable.")
    scope_for_user(db, user)
    now = datetime.now(timezone.utc)
    user_message = MessageChat(
        session_id=session.id,
        role="journaliste",
        contenu=question,
        citations=[],
        horodatage=now,
    )
    db.add(user_message)
    selected_language = resolve_language(language or user.response_language, question)
    answer, citations, chronology = build_research_answer(db, question, use_openrouter=True, language=selected_language)
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
