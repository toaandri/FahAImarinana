import hashlib
import json
from ..core.rbac import Permission as P,authorize
from ..core.errors import ConflictError,ForbiddenError,NotFoundError
from ..core.security import now
from ..database.scope import scope_for_user
from ..repositories import DraftRepository
from ..schemas import PublishRequest


def record_revision(db,draft,actor_id,event):
    from ..models import DraftRevision
    from ..schemas.editorial import DraftVersionRead
    db.flush()
    snapshot=DraftVersionRead.model_validate(draft).model_dump(mode='json')
    snapshot['approved_payload']=draft.approved_payload
    snapshot['validated_at']=draft.validated_at.isoformat() if draft.validated_at else None
    db.add(DraftRevision(draft_id=draft.id,actor_id=actor_id,version=draft.version,
                         event=event,snapshot=snapshot))


def payload_hash(payload):
    data=PublishRequest.model_validate(payload).model_dump()
    return hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def locked_draft(db,user,identifier,permission):
    authorize(user,permission); scope_for_user(db,user)
    draft=DraftRepository(db).lock(identifier)
    if draft is None:
        raise NotFoundError('Brouillon introuvable.')
    if draft.statut!='En_Attente':
        raise ConflictError('Ce brouillon ne peut plus être modifié ou validé.')
    return draft


def clear_validation(draft):
    draft.validated_version=None; draft.validated_by_id=None; draft.validated_at=None
    draft.approved_payload=None; draft.approved_payload_hash=None


def edit_draft(db,user,identifier,payload):
    draft=locked_draft(db,user,identifier,P.DRAFT_EDIT)
    if draft.version!=payload.expected_version:
        raise ConflictError('Le brouillon a changé ; recharger sa version.')
    record_revision(db,draft,user.id,'before_edit')
    for key in ('titre_suggere','synthese_ia'):
        if getattr(payload,key) is not None:
            setattr(draft,key,getattr(payload,key))
    draft.version+=1; clear_validation(draft)
    record_revision(db,draft,user.id,'edited')
    db.commit()
    return draft


def review_draft(db,user,identifier,payload):
    draft=locked_draft(db,user,identifier,P.DRAFT_REVIEW)
    if draft.version!=payload.expected_version:
        raise ConflictError('La version relue est périmée.')
    draft.review_notes=payload.notes
    clear_validation(draft)
    if payload.decision=='rejected':
        draft.statut='Rejete'
    record_revision(db,draft,user.id,'reviewed')
    db.commit()
    return draft


def validate_draft(db,user,identifier,payload):
    draft=locked_draft(db,user,identifier,P.VERSION_VALIDATE)
    if user.dataset=='quarantine':
        raise ForbiddenError('Les archives non classifiées ne peuvent pas être validées pour publication.')
    if draft.version!=payload.expected_version:
        raise ConflictError('La version à valider est périmée.')
    approved=PublishRequest.model_validate(payload.model_dump()).model_dump()
    draft.approved_payload=approved
    draft.approved_payload_hash=payload_hash(approved)
    draft.validated_version=draft.version
    draft.validated_by_id=user.id; draft.validated_at=now()
    record_revision(db,draft,user.id,'validated')
    db.commit()
    return draft
