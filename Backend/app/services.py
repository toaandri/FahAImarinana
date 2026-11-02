import re
import unicodedata
from datetime import datetime, timedelta, timezone
import os
from hashlib import sha256

import bcrypt

from jose import JWTError, jwt
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .models import (
    ArticleCertifie,
    ContactJournaliste,
    DocumentRecherche,
    DraftIA,
    HistoriqueSms,
    MessageChat,
    SessionChat,
    SignalBrut,
    SourceSurveillee,
    Utilisateur,
)

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
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


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


def create_draft(db: Session, signal: SignalBrut, sources: list[dict]) -> DraftIA:
    concordant = sum(1 for source in sources if source["concorde"])
    official = sum(1 for source in sources if source["officielle"])
    total = len(sources)
    score = 20.0 if not total else min(95.0, 35 + concordant / total * 45 + official * 10)
    first_sentence = re.split(r"(?<=[.!?])\s+", signal.contenu_normalise)[0]
    title = first_sentence[:247] + "..." if len(first_sentence) > 250 else first_sentence
    summary = (
        f"Signal détecté le {signal.horodatage_publication.isoformat()}. "
        f"{signal.contenu_normalise} "
        "Cette synthèse est une pré-analyse IA et doit être relue par un journaliste."
    )
    draft = DraftIA(
        signal_id=signal.id,
        titre_suggere=title or "Signal sans titre",
        synthese_ia=summary,
        score_credibilite_indicatif=round(score, 2),
        sources_croisees=sources,
        statut="En_Attente",
        horodatage=datetime.now(timezone.utc),
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


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


def create_access_token(user: Utilisateur) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user.id), "role": user.role, "iat": now, "exp": now + timedelta(hours=8)},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def authenticate_token(db: Session, token: str) -> Utilisateur:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError) as exc:
        raise ValueError("Jeton d'authentification invalide.") from exc
    user = db.get(Utilisateur, user_id)
    if user is None or not user.actif:
        raise ValueError("Utilisateur inactif ou introuvable.")
    return user


def password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def password_matches(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def publish_draft(
    db: Session,
    draft: DraftIA,
    user: Utilisateur,
    payload,
) -> ArticleCertifie:
    if user.role not in {"Journaliste", "Editeur"}:
        raise ValueError("Seuls les journalistes et éditeurs peuvent publier.")
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


def answer_citizen_sms(db: Session, payload) -> tuple[str, str]:
    query = normalize_text(payload.message)
    words = [word for word in query.casefold().split() if len(word) >= 4][:8]
    articles = db.scalars(
        select(ArticleCertifie).where(
            or_(*[ArticleCertifie.corps_article.ilike(f"%{word}%") for word in words])
        ).limit(1)
    ).all() if words else []
    if articles:
        response, status = articles[0].contenu_optimise_sms, "Trouve"
    else:
        response, status = SECURITY_RESPONSE, "Non_Trouve"
    db.add(HistoriqueSms(
        numero_expediteur=payload.numero_expediteur,
        message_recu=payload.message,
        message_envoye=response,
        horodatage=datetime.now(timezone.utc),
        statut_reponse=status,
    ))
    db.commit()
    return response, status


def send_sms_via_gateway(phone: str, message: str) -> None:
    # Placeholder gateway; replace with real SMS provider integration.
    print(f"[SMS GATEWAY] to={phone} message={message}")


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


def _tokenize(value: str) -> list[str]:
    return [token for token in re.findall(r"\w{4,}", value.casefold())]


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
