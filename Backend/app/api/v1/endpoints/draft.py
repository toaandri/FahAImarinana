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


@router.get('/{draft_id}/version',response_model=DraftVersionRead)
def get_version(draft_id: int,db: Session=Depends(get_db),user: Utilisateur=Depends(require_permission(P.DRAFT_READ))):
    return get_draft(draft_id,db,user)


@router.patch('/{draft_id}',response_model=DraftVersionRead)
def update_draft(draft_id: int,payload: DraftUpdate,db: Session=Depends(get_db),
                 user: Utilisateur=Depends(require_permission(P.DRAFT_EDIT))):
    return edit_draft(db,user,draft_id,payload)
