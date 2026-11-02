from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import journalist_or_editor
from ..models import DraftIA, Utilisateur
from ..schemas import DraftRead

router = APIRouter(prefix="/drafts", tags=["Brouillons IA"])


@router.get("/{draft_id}", response_model=DraftRead)
def get_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(journalist_or_editor),
):
    draft = db.get(DraftIA, draft_id)
    if draft is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brouillon introuvable.",
        )
    return draft
