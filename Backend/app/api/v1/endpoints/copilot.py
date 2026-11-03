from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from ....database import get_db
from ....core.permissions import require_permission
from ....core.rbac import Permission as P
from ....core.errors import NotFoundError
from ....models import Utilisateur
from starlette.concurrency import run_in_threadpool
from ....schemas import ChatMessageRead, ChatSessionCreate, ChatSessionRead, ResearchAnswer, ResearchQuestion
from ....schemas.research import TranslationRequest, TranslationRead
from ....services.translation import translate_answer
from ....utils.languages import resolve_language
from ....repositories import ArticleRepository, SignalRepository
from ....services.chat import ask_copilot, create_chat_session, get_chat_messages, list_chat_sessions
from ....services.research import build_research_answer, index_certified_article
from ....services.notifications import alert_journalists
from ....integrations.sms.gateway import SmsGateway, get_sms_gateway
from ....integrations.notifications.websocket import alert_manager

router = APIRouter(prefix="/copilot", tags=["Copilot IA"])


@router.post("/sessions", response_model=ChatSessionRead, status_code=status.HTTP_201_CREATED)
def create_session(payload: ChatSessionCreate, db: Session = Depends(get_db),
                   user: Utilisateur = Depends(require_permission(P.RESEARCH_RUN))):
    return create_chat_session(db, user, payload.titre)


@router.get("/sessions", response_model=list[ChatSessionRead])
def list_sessions(db: Session = Depends(get_db), user: Utilisateur = Depends(require_permission(P.RESEARCH_RUN))):
    return list_chat_sessions(db, user)


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageRead])
def list_messages(session_id: int, db: Session = Depends(get_db),
                  user: Utilisateur = Depends(require_permission(P.RESEARCH_RUN))):
    return get_chat_messages(db, session_id, user)


@router.post("/sessions/{session_id}/ask", response_model=ResearchAnswer)
def ask(session_id: int, payload: ResearchQuestion, db: Session = Depends(get_db),
        user: Utilisateur = Depends(require_permission(P.RESEARCH_RUN))):
    _, message, citations, chronology = ask_copilot(db, user, session_id, payload.question, language=payload.language)
    return ResearchAnswer(reponse=message.contenu, citations=citations, chronologie=chronology)


@router.post("/research", response_model=ResearchAnswer)
def research(payload: ResearchQuestion, db: Session = Depends(get_db),
             user: Utilisateur = Depends(require_permission(P.RESEARCH_RUN))):
    language = resolve_language(payload.language or user.response_language, payload.question)
    answer, citations, chronology = build_research_answer(db, payload.question, use_openrouter=True, language=language)
    return ResearchAnswer(reponse=answer, citations=citations, chronologie=chronology)


@router.post('/translate', response_model=TranslationRead)
def translate(payload: TranslationRequest, response: Response,
              user: Utilisateur = Depends(require_permission(P.RESEARCH_RUN))):
    response.headers['Cache-Control'] = 'no-store'
    return translate_answer(payload.text, payload.target_language)


@router.post("/index/articles")
def index_articles(db: Session = Depends(get_db), user: Utilisateur = Depends(require_permission(P.INDEX_WRITE))):
    articles = ArticleRepository(db).published()
    try:
        for article in articles:
            index_certified_article(db, article, commit=False)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"indexed": len(articles)}


def _send_alert(db: Session, signal_id: int, gateway: SmsGateway):
    signal = SignalRepository(db).get(signal_id)
    if signal is None:
        raise NotFoundError("Signal introuvable.")
    return alert_journalists(db, signal, gateway.send)


@router.post("/alerts/signal/{signal_id}")
async def trigger_alert(signal_id: int, db: Session = Depends(get_db),
                        user: Utilisateur = Depends(require_permission(P.ALERTS_SEND)),
                        gateway: SmsGateway = Depends(get_sms_gateway)):
    sent = await run_in_threadpool(_send_alert, db, signal_id, gateway)
    # Phone numbers remain in the legacy authorized response, never in broadcasts.
    await alert_manager.broadcast({"type": "alert", "signal_id": signal_id, "sent_count": len(sent)}, scope=(user.newsroom_id, user.dataset))
    return {"signal_id": signal_id, "sent": sent}
