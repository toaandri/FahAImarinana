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
from ..integrations.ai.gemini import GeminiUnavailableError, generate_draft, research_web

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
def index_certified_article(db: Session, article: ArticleCertifie) -> DocumentRecherche:
    existing = db.scalar(
        select(DocumentRecherche).where(DocumentRecherche.url == f"article:{article.id}")
    )
    if existing is not None:
        existing.titre = article.titre_final
        existing.contenu = article.corps_article
        existing.est_certifie = True
        db.commit()
        db.refresh(existing)
        return existing
    document = DocumentRecherche(
        titre=article.titre_final,
        contenu=article.corps_article,
        url=f"article:{article.id}",
        est_certifie=True,
        cree_le=article.horodatage_validation,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def search_knowledge_base(db: Session, question: str, limit: int = 5) -> list[dict]:
    terms = _tokenize(question)
    if not terms:
        return []
    documents = db.scalars(
        select(DocumentRecherche).where(DocumentRecherche.est_certifie.is_(True))
    ).all()
    scored = []
    lowered_question = question.casefold()
    for document in documents:
        haystack = f"{document.titre} {document.contenu}".casefold()
        score = sum(haystack.count(term) for term in terms)
        if score > 0:
            scored.append((score, document))
    scored.sort(key=lambda item: item[0], reverse=True)
    results = []
    for score, document in scored[:limit]:
        results.append(
            {
                "id": document.id,
                "titre": document.titre,
                "extrait": document.contenu[:600],
                "url": document.url,
                "date": document.cree_le.isoformat() if document.cree_le else None,
                "score": score,
            }
        )
    return results


def build_research_answer(db: Session, question: str) -> tuple[str, list[dict], list[dict]]:
    if get_settings().gemini_api_key:
        try:
            answer, citations = research_web(question)
            return answer, citations, []
        except GeminiUnavailableError:
            pass
    results = search_knowledge_base(db, question)
    citations = [
        {"titre": item["titre"], "url": item["url"], "date": item["date"], "extrait": item["extrait"]}
        for item in results
    ]
    chronology = sorted(
        [{"date": item["date"], "titre": item["titre"], "extrait": item["extrait"]} for item in results],
        key=lambda item: item["date"] or "",
    )
    if not results:
        answer = (
            "Aucun document certifié ne correspond à cette question. "
            "Sujet en cours de vérification par nos journalistes."
        )
    else:
        context = "\n".join(f"- {item['titre']}: {item['extrait']}" for item in results)
        answer = (
            f"Réponse contextuelle basée sur {len(results)} source(s) certifiée(s).\n"
            f"Question: {question}\n"
            f"Contexte:\n{context}\n"
            "Cette synthèse est une pré-analyse IA et doit être relue par un journaliste."
        )
    return answer, citations, chronology
