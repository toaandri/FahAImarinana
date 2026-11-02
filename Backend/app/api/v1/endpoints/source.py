from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from ....database import get_db
from ....core.permissions import journalist_or_editor
from ....models import Utilisateur
from ....schemas import SourceCreate, SourceRead
from ....services.sources import create_source as save_source

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.post("", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
def create_source(payload: SourceCreate, db: Session = Depends(get_db),
                  _: Utilisateur = Depends(journalist_or_editor)):
    return save_source(db, payload)
