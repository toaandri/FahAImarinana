from ..core.rbac import authorize, Permission as P
from ..database.scope import scope_for_user
from ..core.errors import ValidationDomainError
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..integrations.maharavo.research import ResearchProvider
from ..integrations.maharavo.errors import MaharavoNotConfigured
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
    authorize(user,P.RESEARCH_RUN)
    scope_for_user(db, user)
    # The repository contains no separate Maharavo server or documented wire protocol.
    # Never issue a Gemini request or fabricate a successful job under this name.
    raise MaharavoNotConfigured()


def record_media_analysis(db: Session, user: Utilisateur, payload) -> AnalyseMediaMaharavo:
    authorize(user,P.ANALYSIS_WRITE)
    scope_for_user(db, user)
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
    authorize(user,P.ANALYSIS_WRITE)
    if payload.validation_editoriale != "non_evalue":
        authorize(user,P.VERSION_VALIDATE)
    scope_for_user(db, user)
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
