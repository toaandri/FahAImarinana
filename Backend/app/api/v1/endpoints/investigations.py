from fastapi import APIRouter,Depends,Query
from pydantic import BaseModel,ConfigDict,Field,HttpUrl
from sqlalchemy import select,or_
from sqlalchemy.orm import Session
from ....database import get_db
from ....core.permissions import require_permission
from ....core.rbac import Permission as P,authorize
from ....core.errors import NotFoundError
from ....models import User,Case,Evidence,Contribution,Claim,ClaimEvidence,Source,Draft,ResearchJob
from ....repositories import CaseRepository
from ....schemas.investigations import (CaseCreate,CaseRead,CaseUpdate,EvidenceCreate,EvidenceRead,
    ClaimCreate,ClaimRead,EvidenceLinkCreate,EvidenceLinkRead,ManualDraftCreate,LocalResearchCreate,ResearchRead)
from ....schemas.editorial import DraftVersionRead
from ....schemas.sources import SourceRead
from ....services import investigations as service
from ....core.rbac import Permission as P
from typing import Literal

router=APIRouter(tags=['Dossiers et contributions'])


@router.post('/cases',response_model=CaseRead,status_code=201)
def create_case(payload: CaseCreate,db: Session=Depends(get_db),user: User=Depends(require_permission(P.CASE_CREATE))):
    authorize(user,P.CASE_CREATE)
    case=Case(**payload.model_dump(),created_by_id=user.id)
    db.add(case); db.commit()
    return case


@router.get('/cases',response_model=list[CaseRead])
def cases(db: Session=Depends(get_db),user: User=Depends(require_permission(P.CASE_READ)),
          limit: int=Query(default=50,ge=1,le=200),offset: int=Query(default=0,ge=0),
          q: str=Query(default='',max_length=250),
          status: Literal['open','investigating','review','closed','archived']|None=None):
    statement=select(Case)
    if q.strip():
        statement=statement.where(or_(Case.title.icontains(q.strip(),autoescape=True),
                                      Case.description.icontains(q.strip(),autoescape=True)))
    if status is not None:
        statement=statement.where(Case.status==status)
    return list(db.scalars(statement.order_by(Case.id.desc()).limit(limit).offset(offset)))


@router.get('/cases/{case_id}',response_model=CaseRead)
def case(case_id: int,db: Session=Depends(get_db),user: User=Depends(require_permission(P.CASE_READ))):
    result=CaseRepository(db).get(case_id)
    if result is None:
        raise NotFoundError('Dossier introuvable.')
    return result


@router.post('/cases/{case_id}/evidence',response_model=EvidenceRead,status_code=201)
def evidence(case_id: int,payload: EvidenceCreate,db: Session=Depends(get_db),
             user: User=Depends(require_permission(P.EVIDENCE_ADD))):
    return service.add_evidence(db,user,case_id,payload)


@router.patch('/cases/{case_id}',response_model=CaseRead)
def update_case(case_id: int,payload: CaseUpdate,db: Session=Depends(get_db),
                user: User=Depends(require_permission(P.CASE_EDIT))):
    return service.update_case(db,user,case_id,payload)


@router.post('/cases/{case_id}/archive',response_model=CaseRead)
def archive_case(case_id: int,db: Session=Depends(get_db),
                 user: User=Depends(require_permission(P.CASE_EDIT))):
    record=service.get_case(db,case_id,writable=True)
    record.status='archived'; db.commit()
    return record


@router.post('/cases/{case_id}/claims',response_model=ClaimRead,status_code=201)
def add_claim(case_id: int,payload: ClaimCreate,db: Session=Depends(get_db),
              user: User=Depends(require_permission(P.CLAIM_ADD))):
    return service.add_claim(db,user,case_id,payload)


def case_items(db,case_id,model,limit,offset):
    service.get_case(db,case_id)
    return list(db.scalars(select(model).where(model.case_id==case_id).order_by(model.id).limit(limit).offset(offset)))


@router.get('/cases/{case_id}/claims',response_model=list[ClaimRead])
def list_claims(case_id: int,db: Session=Depends(get_db),user: User=Depends(require_permission(P.CASE_READ)),
                limit: int=Query(default=50,ge=1,le=200),offset: int=Query(default=0,ge=0)):
    return case_items(db,case_id,Claim,limit,offset)


@router.get('/cases/{case_id}/evidence',response_model=list[EvidenceRead])
def list_evidence(case_id: int,db: Session=Depends(get_db),user: User=Depends(require_permission(P.CASE_READ)),
                  limit: int=Query(default=50,ge=1,le=200),offset: int=Query(default=0,ge=0)):
    return case_items(db,case_id,Evidence,limit,offset)


@router.post('/cases/{case_id}/claims/{claim_id}/evidence',response_model=EvidenceLinkRead,status_code=201)
def link_evidence(case_id: int,claim_id: int,payload: EvidenceLinkCreate,db: Session=Depends(get_db),
                  user: User=Depends(require_permission(P.EVIDENCE_ADD))):
    return service.link_evidence(db,user,case_id,claim_id,payload)


@router.get('/cases/{case_id}/claims/{claim_id}/evidence',response_model=list[EvidenceLinkRead])
def claim_evidence(case_id: int,claim_id: int,db: Session=Depends(get_db),
                   user: User=Depends(require_permission(P.CASE_READ)),
                   limit: int=Query(default=50,ge=1,le=200),offset: int=Query(default=0,ge=0)):
    service.get_case(db,case_id)
    if db.scalar(select(Claim.id).where(Claim.id==claim_id,Claim.case_id==case_id)) is None:
        raise NotFoundError('Affirmation introuvable.')
    return list(db.scalars(select(ClaimEvidence).where(ClaimEvidence.case_id==case_id,ClaimEvidence.claim_id==claim_id)
        .order_by(ClaimEvidence.id).limit(limit).offset(offset)))


@router.get('/cases/{case_id}/sources',response_model=list[SourceRead])
def available_sources(case_id: int,db: Session=Depends(get_db),user: User=Depends(require_permission(P.CASE_READ)),
                      limit: int=Query(default=50,ge=1,le=200),offset: int=Query(default=0,ge=0)):
    service.get_case(db,case_id)
    return list(db.scalars(select(Source).order_by(Source.id).limit(limit).offset(offset)))


@router.post('/cases/{case_id}/drafts',response_model=DraftVersionRead,status_code=201)
def manual_draft(case_id: int,payload: ManualDraftCreate,db: Session=Depends(get_db),
                 user: User=Depends(require_permission(P.DRAFT_EDIT))):
    return service.create_manual_draft(db,user,case_id,payload)


@router.get('/cases/{case_id}/drafts',response_model=list[DraftVersionRead])
def case_drafts(case_id: int,db: Session=Depends(get_db),user: User=Depends(require_permission(P.CASE_READ)),
                 limit: int=Query(default=50,ge=1,le=200),offset: int=Query(default=0,ge=0)):
    authorize(user,P.DRAFT_READ)
    return case_items(db,case_id,Draft,limit,offset)


@router.post('/cases/{case_id}/research',response_model=ResearchRead,status_code=201)
def local_research(case_id: int,payload: LocalResearchCreate,db: Session=Depends(get_db),
                   user: User=Depends(require_permission(P.RESEARCH_RUN))):
    return service.local_research(db,user,case_id,payload)


@router.get('/cases/{case_id}/research',response_model=list[ResearchRead])
def case_research(case_id: int,db: Session=Depends(get_db),user: User=Depends(require_permission(P.CASE_READ)),
                   limit: int=Query(default=50,ge=1,le=200),offset: int=Query(default=0,ge=0)):
    return case_items(db,case_id,ResearchJob,limit,offset)


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
