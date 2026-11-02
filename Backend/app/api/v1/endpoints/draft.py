from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ....database import get_db
from ....core.permissions import journalist_or_editor
from ....core.errors import NotFoundError
from ....models import Utilisateur
from ....repositories import DraftRepository
from ....schemas import DraftRead

router = APIRouter(prefix="/drafts", tags=["Brouillons IA"])


@router.get("/{draft_id}", response_model=DraftRead)
def get_draft(draft_id: int, db: Session = Depends(get_db),
              _: Utilisateur = Depends(journalist_or_editor)):
    draft = DraftRepository(db).get(draft_id)
    if draft is None:
        raise NotFoundError("Brouillon introuvable.")
    return draft
