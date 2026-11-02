from fastapi import APIRouter,Depends
from pydantic import BaseModel,ConfigDict,Field,HttpUrl
from sqlalchemy import select
from sqlalchemy.orm import Session
from ....database import get_db
from ....core.permissions import require_permission
from ....core.rbac import Permission as P,authorize
from ....core.errors import NotFoundError
from ....models import User,Case,Evidence,Contribution
from ....repositories import CaseRepository

router=APIRouter(tags=['Dossiers et contributions'])


class CaseCreate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    title: str=Field(min_length=1,max_length=250)
    description: str=Field(default='',max_length=20000)


class CaseRead(CaseCreate):
    model_config=ConfigDict(from_attributes=True)
    id: int
    status: str


class EvidenceCreate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    title: str=Field(min_length=1,max_length=250)
    content: str=Field(min_length=1,max_length=100000)
    kind: str=Field(pattern='^(document|image|video|audio|url|testimony)$')


class EvidenceRead(EvidenceCreate):
    model_config=ConfigDict(from_attributes=True)
    id: int
    case_id: int


@router.post('/cases',response_model=CaseRead,status_code=201)
def create_case(payload: CaseCreate,db: Session=Depends(get_db),user: User=Depends(require_permission(P.CASE_CREATE))):
    authorize(user,P.CASE_CREATE)
    case=Case(**payload.model_dump(),created_by_id=user.id)
    db.add(case); db.commit()
    return case


@router.get('/cases',response_model=list[CaseRead])
def cases(db: Session=Depends(get_db),user: User=Depends(require_permission(P.CASE_READ))):
    return CaseRepository(db).list()


@router.get('/cases/{case_id}',response_model=CaseRead)
def case(case_id: int,db: Session=Depends(get_db),user: User=Depends(require_permission(P.CASE_READ))):
    result=CaseRepository(db).get(case_id)
    if result is None:
        raise NotFoundError('Dossier introuvable.')
    return result


@router.post('/cases/{case_id}/evidence',response_model=EvidenceRead,status_code=201)
def evidence(case_id: int,payload: EvidenceCreate,db: Session=Depends(get_db),
             user: User=Depends(require_permission(P.EVIDENCE_ADD))):
    if CaseRepository(db).get(case_id) is None:
        raise NotFoundError('Dossier introuvable.')
    record=Evidence(case_id=case_id,**payload.model_dump(),confidentiality='confidential')
    db.add(record); db.commit()
    return record


class Submission(BaseModel):
    model_config=ConfigDict(extra='forbid')
    content: str=Field(min_length=1,max_length=20000)
    reference_url: HttpUrl|None=Field(default=None,max_length=500)


class ContributionRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: int
    kind: str
    content: str
    status: str


@router.post('/contributions/signals',response_model=ContributionRead,status_code=201)
def submit_signal(payload: Submission,db: Session=Depends(get_db),
                  user: User=Depends(require_permission(P.CONTRIBUTION_ADD))):
    record=Contribution(submitted_by_id=user.id,kind='signal',content=payload.content,
        reference_url=str(payload.reference_url) if payload.reference_url else None)
    db.add(record); db.commit()
    return record


def own_submission(db,user,identifier):
    record=db.scalar(select(Contribution).where(Contribution.id==identifier,Contribution.submitted_by_id==user.id))
    if record is None:
        raise NotFoundError('Signalement introuvable.')
    return record


@router.get('/contributions/{contribution_id}',response_model=ContributionRead)
def submission(contribution_id: int,db: Session=Depends(get_db),
               user: User=Depends(require_permission(P.CONTRIBUTION_ADD))):
    return own_submission(db,user,contribution_id)


@router.post('/contributions/{contribution_id}/information',response_model=ContributionRead,status_code=201)
def add_information(contribution_id: int,payload: Submission,db: Session=Depends(get_db),
                    user: User=Depends(require_permission(P.CONTRIBUTION_ADD))):
    parent=own_submission(db,user,contribution_id)
    record=Contribution(submitted_by_id=user.id,parent_id=parent.id,kind='information',content=payload.content,
        reference_url=str(payload.reference_url) if payload.reference_url else None)
    db.add(record); db.commit()
    return record
