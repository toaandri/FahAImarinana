from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import journalist_or_editor
from ..models import SourceSurveillee, Utilisateur
from ..schemas import SourceCreate, SourceRead

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.post("", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
def create_source(
    payload: SourceCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(journalist_or_editor),
):
    source = SourceSurveillee(
        nom=payload.nom,
        type=payload.type,
        url=str(payload.url),
        frequence_scan_secondes=payload.frequence_scan_secondes,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source
