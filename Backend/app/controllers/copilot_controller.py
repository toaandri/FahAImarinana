import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import journalist_or_editor
from ..models import SessionChat, Utilisateur
from ..notifications import alert_manager
from ..schemas import (
    ChatMessageRead,
    ChatSessionCreate,
    ChatSessionRead,
    ResearchAnswer,
    ResearchQuestion,
)
from ..services import (
    ask_copilot,
    build_research_answer,
    create_chat_session,
    get_chat_messages,
    index_certified_article,
    list_chat_sessions,
    send_sms_via_gateway,
)
from ..models import ArticleCertifie, SignalBrut
from ..services import alert_journalists

router = APIRouter(prefix="/copilot", tags=["Copilot IA"])


@router.post("/sessions", response_model=ChatSessionRead, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: ChatSessionCreate,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(journalist_or_editor),
):
    return create_chat_session(db, user, payload.titre)


@router.get("/sessions", response_model=list[ChatSessionRead])
def list_sessions(db: Session = Depends(get_db), user: Utilisateur = Depends(journalist_or_editor)):
    return list_chat_sessions(db, user)


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageRead])
def list_messages(
    session_id: int,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(journalist_or_editor),
):
    try:
        return get_chat_messages(db, session_id, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/ask", response_model=ResearchAnswer)
def ask(
    session_id: int,
    payload: ResearchQuestion,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(journalist_or_editor),
):
    try:
        _, assistant_message, citations, chronology = ask_copilot(db, user, session_id, payload.question)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ResearchAnswer(reponse=assistant_message.contenu, citations=citations, chronologie=chronology)


@router.post("/research", response_model=ResearchAnswer)
def research(payload: ResearchQuestion, db: Session = Depends(get_db), user: Utilisateur = Depends(journalist_or_editor)):
    answer, citations, chronology = build_research_answer(db, payload.question)
    return ResearchAnswer(reponse=answer, citations=citations, chronologie=chronology)


@router.post("/index/articles", status_code=status.HTTP_200_OK)
def index_articles(db: Session = Depends(get_db), user: Utilisateur = Depends(journalist_or_editor)):
    articles = list(db.scalars(select(ArticleCertifie)))
    count = 0
    for article in articles:
        index_certified_article(db, article)
        count += 1
    return {"indexed": count}


@router.post("/alerts/signal/{signal_id}", status_code=status.HTTP_200_OK)
async def trigger_alert(signal_id: int, db: Session = Depends(get_db), user: Utilisateur = Depends(journalist_or_editor)):
    signal = db.get(SignalBrut, signal_id)
    if signal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signal introuvable.")
    sent = alert_journalists(db, signal, send_sms_via_gateway)
    await alert_manager.broadcast({"type": "alert", "signal_id": signal_id, "sent": sent})
    return {"signal_id": signal_id, "sent": sent}