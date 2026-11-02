from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SourceSurveillee
from ..schemas import SourceCreate, SourceRead

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.post("", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)):
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
