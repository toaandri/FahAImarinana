import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..database.scope import scope_for_user, set_scope
from ..core.rbac import authorize, Permission as P
from .draft_workflow import payload_hash
from ..models import ArticleCertifie, DraftIA, Utilisateur, CorrectionAudit
from ..core.errors import ConflictError, NotFoundError, ForbiddenError
from ..repositories import ArticleRepository, DraftRepository
logger = logging.getLogger(__name__)
from .research import index_certified_article

def publish_draft(db: Session, draft: DraftIA, user: Utilisateur, payload) -> ArticleCertifie:
    authorize(user,P.PUBLISH)
    scope_for_user(db, user)
    if user.dataset == "quarantine":
        raise ForbiddenError("Les archives non classifiées doivent être revues avant publication.")
    locked = DraftRepository(db).lock(draft.id)
    if locked is None:
        raise NotFoundError("Brouillon introuvable.")
    if locked.statut != "En_Attente" or ArticleRepository(db).by_draft(locked.id):
        raise ConflictError("Ce brouillon ne peut plus être publié.")
    if locked.validated_version != locked.version or locked.approved_payload_hash != payload_hash(payload):
        raise ConflictError("Une validation éditoriale de cette version et de ce contenu exact est requise.")
    article = ArticleCertifie(
        status="published", confidentiality="public", published_at=datetime.now(timezone.utc),
        draft_id=locked.id, titre_final=payload.titre_final, corps_article=payload.corps_article,
        categorie=payload.categorie, statut_verification=payload.statut_verification,
        id_journaliste_validateur=locked.validated_by_id, horodatage_validation=datetime.now(timezone.utc),
        contenu_optimise_sms=payload.contenu_optimise_sms,
    )
    locked.statut = "En_Cours"  # legacy persisted value and response contract
    db.add(article)
    try:
        db.flush()
        index_certified_article(db, article, commit=False)
        db.add(CorrectionAudit(publication_id=article.id, actor_id=user.id,
                               action="published", reason="Validation éditoriale humaine.",
                               after={"revision": article.revision, "title": article.titre_final}))
        from .draft_workflow import record_revision
        record_revision(db,locked,user.id,'published')
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(article)
    return article
