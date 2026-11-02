"""Audited publication changes. Only approved public fields can be corrected."""
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..core.rbac import authorize, Permission as P
from ..core.errors import ForbiddenError, ConflictError, NotFoundError, ValidationDomainError
from ..database.scope import scope_for_user
from ..models import Publication, CorrectionAudit
from ..repositories import ResearchRepository
from ..schemas import PublishRequest
from .research import index_certified_article

PUBLIC_FIELDS = ('titre_final','corps_article','categorie','statut_verification','contenu_optimise_sms')


def _locked(db, user, publication_id, reason):
    authorize(user,P.CORRECT)
    if not reason.strip() or len(reason) > 5000:
        raise ValidationDomainError('Une justification de 1 à 5000 caractères est requise.')
    scope_for_user(db,user)
    publication=db.scalar(select(Publication).where(Publication.id==publication_id)
                          .with_for_update().execution_options(populate_existing=True))
    if publication is None:
        raise NotFoundError('Publication introuvable.')
    if publication.status!='published':
        raise ConflictError('La publication ne peut plus être modifiée dans cet état.')
    return publication


def correct_publication(db: Session, user, publication_id: int, payload: PublishRequest, *, reason: str):
    payload=PublishRequest.model_validate(payload)
    publication=_locked(db,user,publication_id,reason)
    before={field:getattr(publication,field) for field in PUBLIC_FIELDS}
    before['revision']=publication.revision
    for field in PUBLIC_FIELDS:
        setattr(publication,field,getattr(payload,field))
    publication.revision+=1
    publication.id_journaliste_validateur=user.id
    publication.horodatage_validation=datetime.now(timezone.utc)
    after={field:getattr(publication,field) for field in PUBLIC_FIELDS}
    after['revision']=publication.revision
    db.add(CorrectionAudit(publication_id=publication.id,actor_id=user.id,action='corrected',reason=reason,
                           before=before,after=after))
    try:
        index_certified_article(db,publication,commit=False)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return publication


def withdraw_publication(db: Session, user, publication_id: int, *, reason: str):
    publication=_locked(db,user,publication_id,reason)
    publication.status='withdrawn'
    publication.confidentiality='private'
    db.add(CorrectionAudit(publication_id=publication.id,actor_id=user.id,action='withdrawn',reason=reason,
                           before={'status':'published'},after={'status':'withdrawn'}))
    try:
        document=ResearchRepository(db).by_article(publication.id)
        if document is not None:
            document.est_certifie=False
        db.commit()
    except Exception:
        db.rollback()
        raise
    return publication
