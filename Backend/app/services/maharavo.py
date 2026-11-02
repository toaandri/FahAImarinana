from ..core.config import get_settings
from ..core.errors import ValidationDomainError
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..integrations.ai.gemini import GeminiUnavailableError
from ..integrations.maharavo.research import ResearchProvider, GeminiResearchProvider
from ..models import (
    AnalyseMediaMaharavo,
    EvaluationConfianceMaharavo,
    RechercheMaharavo,
    Utilisateur,
)


def run_research(
    db: Session,
    user: Utilisateur,
    sujet: str,
    questions: list[str],
    periode: str | None,
    langues: list[str],
    territoire: str | None,
    provider: ResearchProvider | None = None,
) -> RechercheMaharavo:
    started = datetime.now(timezone.utc)
    prompt = "Sujet: " + sujet
    if questions:
        prompt += "\nQuestions: " + "; ".join(questions)
    if periode:
        prompt += "\nPériode: " + periode
    if langues:
        prompt += "\nLangues: " + ", ".join(langues)
    if territoire:
        prompt += "\nTerritoire: " + territoire
    job = RechercheMaharavo(
        utilisateur_id=user.id,
        sujet=sujet,
        questions=questions,
        periode=periode,
        langues=langues,
        territoire=territoire,
        requetes=[prompt],
        documents_ouverts=[],
        citations=[],
        erreurs=[],
        statut="en_cours",
        modele=get_settings().gemini_model,
        debut=started,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    try:
        synthesis, citations = (provider or GeminiResearchProvider()).research(prompt)
        job.synthese = synthesis
        job.citations = citations
        job.documents_ouverts = citations[:5]
        job.statut = "terminee" if citations else "partielle"
    except GeminiUnavailableError as exc:
        job.erreurs = [str(exc)]
        job.statut = "echouee"
    job.fin = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return job


def record_media_analysis(db: Session, user: Utilisateur, payload) -> AnalyseMediaMaharavo:
    analysis = AnalyseMediaMaharavo(
        utilisateur_id=user.id,
        type_media=payload.type_media,
        reference_originale=payload.reference_originale,
        empreinte_sha256=payload.empreinte_sha256.lower(),
        outil=payload.outil,
        version_outil=payload.version_outil,
        observations=payload.observations,
        indice_indicatif=payload.indice_indicatif,
        limites=payload.limites
        or ["Un indice ne constitue pas une conclusion de véracité ou de manipulation."],
        cree_le=datetime.now(timezone.utc),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def record_confidence(
    db: Session, user: Utilisateur, payload
) -> EvaluationConfianceMaharavo:
    if (
        payload.identite_source == "eleve"
        or payload.solidite_preuves == "eleve"
    ) and payload.conclusion == "non_verifiable":
        raise ValidationDomainError("Une conclusion non vérifiable ne peut pas avoir une solidité élevée.")
    evaluation = EvaluationConfianceMaharavo(
        utilisateur_id=user.id,
        objet_type=payload.objet_type,
        objet_id=payload.objet_id,
        identite_source=payload.identite_source,
        solidite_preuves=payload.solidite_preuves,
        validation_editoriale=payload.validation_editoriale,
        conclusion=payload.conclusion,
        justification=payload.justification,
        cree_le=datetime.now(timezone.utc),
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation
