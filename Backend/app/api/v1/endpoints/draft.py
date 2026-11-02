from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ....database import get_db
from ....core.permissions import require_permission
from ....core.rbac import Permission as P
from ....core.errors import NotFoundError
from ....models import Utilisateur
from ....repositories import DraftRepository
from ....schemas import DraftRead

router = APIRouter(prefix="/drafts", tags=["Brouillons IA"])


@router.get("/{draft_id}", response_model=DraftRead)
def get_draft(draft_id: int, db: Session = Depends(get_db),
              _: Utilisateur = Depends(require_permission(P.DRAFT_READ))):
    draft = DraftRepository(db).get(draft_id)
    if draft is None:
        raise NotFoundError("Brouillon introuvable.")
    return draft


from ....schemas.editorial import DraftUpdate,DraftVersionRead
from ....services.draft_workflow import edit_draft
from fastapi import Query
from sqlalchemy import select
from ....models import DraftRevision
from ....schemas.investigations import RevisionRead


@router.get('/{draft_id}/history',response_model=list[RevisionRead])
def history(draft_id: int,db: Session=Depends(get_db),user: Utilisateur=Depends(require_permission(P.DRAFT_READ)),
            limit: int=Query(default=50,ge=1,le=200),offset: int=Query(default=0,ge=0)):
    get_draft(draft_id,db,user)
    return list(db.scalars(select(DraftRevision).where(DraftRevision.draft_id==draft_id)
        .order_by(DraftRevision.id).limit(limit).offset(offset)))


@router.post('/{draft_id}/revisions',response_model=DraftVersionRead,status_code=201)
def create_revision(draft_id: int,payload: DraftUpdate,db: Session=Depends(get_db),
                    user: Utilisateur=Depends(require_permission(P.DRAFT_EDIT))):
    # MIDP HttpConnection has no portable PATCH support. Same domain operation,
    # explicit append-revision resource, same version conflict and validation reset.
    return edit_draft(db,user,draft_id,payload)


@router.get('/{draft_id}/version',response_model=DraftVersionRead)
def get_version(draft_id: int,db: Session=Depends(get_db),user: Utilisateur=Depends(require_permission(P.DRAFT_READ))):
    return get_draft(draft_id,db,user)


@router.patch('/{draft_id}',response_model=DraftVersionRead)
def update_draft(draft_id: int,payload: DraftUpdate,db: Session=Depends(get_db),
                 user: Utilisateur=Depends(require_permission(P.DRAFT_EDIT))):
    return edit_draft(db,user,draft_id,payload)
