from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from ....database import get_db
from ....core.permissions import require_permission
from ....core.rbac import Permission as P
from ....models import Utilisateur
from ....schemas import SourceCreate, SourceRead
from ....services.sources import create_source as save_source

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.post("", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
def create_source(payload: SourceCreate, db: Session = Depends(get_db),
                  _: Utilisateur = Depends(require_permission(P.CONNECTORS_MANAGE))):
    return save_source(db, payload)


from pydantic import BaseModel,ConfigDict,Field
from typing import Literal
from ....repositories import SourceRepository
from ....core.errors import NotFoundError


class ConnectorUpdate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    statut: Literal['Actif','Inactif']|None=None
    frequence_scan_secondes: int|None=Field(default=None,ge=60,le=86400)


@router.patch('/{source_id}',response_model=SourceRead)
def update_connector(source_id: int,payload: ConnectorUpdate,db: Session=Depends(get_db),
                     user: Utilisateur=Depends(require_permission(P.CONNECTORS_MANAGE))):
    record=SourceRepository(db).update(source_id,**payload.model_dump(exclude_none=True))
    db.commit()
    return record


from sqlalchemy import select
from ....models import SourceSurveillee


@router.get('',response_model=list[SourceRead])
def list_connectors(db: Session=Depends(get_db),user: Utilisateur=Depends(require_permission(P.CONNECTORS_MANAGE))):
    return list(db.scalars(select(SourceSurveillee).order_by(SourceSurveillee.id).limit(200)))
