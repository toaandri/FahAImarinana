import logging
from sqlalchemy.orm import Session
from ..database.scope import set_scope
from ..models import ArticleCertifie, DocumentRecherche
from ..core.config import get_settings
from ..repositories import ResearchRepository
from ..utils.text import tokenize as _tokenize
logger = logging.getLogger(__name__)
from ..integrations.ai.gemini import GeminiUnavailableError, research_web
from ..integrations.ai.openrouter import OpenRouterUnavailableError, answer_question
from ..utils.languages import expand_research_question

def index_certified_article(db: Session, article: ArticleCertifie, *, commit: bool = True) -> DocumentRecherche:
    set_scope(db, article.newsroom_id, article.dataset)
    document = ResearchRepository(db).by_article(article.id)
    if document is None:
        document = DocumentRecherche(url=f"article:{article.id}", cree_le=article.horodatage_validation)
        db.add(document)
    document.titre = article.titre_final
    document.contenu = article.corps_article
    document.est_certifie = True
    db.flush()
    if commit:
        db.commit()
        db.refresh(document)
    return document



def search_knowledge_base(db: Session, question: str, limit: int = 5) -> list[dict]:
    from .administration import technical_setting
    limit = technical_setting(db,"research_result_limit",limit)
    terms = _tokenize(expand_research_question(question))
    if not terms:
        return []
    documents = ResearchRepository(db).certified()
    scored = []
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


def build_research_answer(db: Session, question: str, *, use_openrouter: bool = False, language: str = 'fr') -> tuple[str, list[dict], list[dict]]:
    results = None
    if use_openrouter and get_settings().openrouter_api_key.get_secret_value().strip():
        results = search_knowledge_base(db, question)
        citations = [
            {"titre": item["titre"], "url": item["url"], "date": item["date"], "extrait": item["extrait"]}
            for item in results
        ]
        try:
            return answer_question(question, citations, language=language), citations, sorted(
                [{"date": item["date"], "titre": item["titre"], "extrait": item["extrait"]} for item in results],
                key=lambda item: item["date"] or "",
            )
        except OpenRouterUnavailableError:
            logger.warning("OpenRouter indisponible ; utilisation du repli de recherche.")
    if get_settings().gemini_api_key.get_secret_value():
        try:
            answer, citations = research_web(question, language=language)
            return answer, citations, []
        except GeminiUnavailableError:
            pass
    if results is None:
        results = search_knowledge_base(db, question)
    citations = [
        {"titre": item["titre"], "url": item["url"], "date": item["date"], "extrait": item["extrait"]}
        for item in results
    ]
    chronology = sorted(
        [{"date": item["date"], "titre": item["titre"], "extrait": item["extrait"]} for item in results],
        key=lambda item: item["date"] or "",
    )
    if language == 'en':
        if not results:
            return ('No certified document matches this question. '
                    'Our journalists are still verifying this topic.'), citations, chronology
        context = "\n".join(f"- {item['titre']}: {item['extrait']}" for item in results)
        return (f"Found {len(results)} certified source(s).\nQuestion: {question}\n"
                f"Sources (original language):\n{context}\n"
                "This preliminary analysis must be reviewed by a journalist."), citations, chronology
    if not results:
        answer = ('Tsy misy antontan-taratasy voamarina mifanaraka amin’ity fanontaniana ity. '
                  'Mbola eo am-panamarinana izany ny mpanao gazety.' if language == 'mg' else (
            "Aucun document certifié ne correspond à cette question. "
            "Sujet en cours de vérification par nos journalistes."
        ))
    else:
        context = "\n".join(f"- {item['titre']}: {item['extrait']}" for item in results)
        answer = ((f"Ireto ny loharano voamarina {len(results)} mifandraika amin’ny fanontaniana.\n"
                   f"Fanontaniana: {question}\nLoharano (teny niandohana):\n{context}\n"
                   "Mbola mila famakiana sy fanamarinana ataon’ny mpanao gazety ity valiny ity.") if language == 'mg' else (
            f"Réponse contextuelle basée sur {len(results)} source(s) certifiée(s).\n"
            f"Question: {question}\n"
            f"Contexte:\n{context}\n"
            "Cette synthèse est une pré-analyse IA et doit être relue par un journaliste."
        ))
    return answer, citations, chronology
