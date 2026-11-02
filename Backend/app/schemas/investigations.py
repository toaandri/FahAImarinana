"""Human input cannot supply verdicts, validators, scope or publication states."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class CaseCreate(Input):
    title: str = Field(min_length=1, max_length=250)
    description: str = Field(default='', max_length=20000)


class CaseRead(CaseCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    updated_at: datetime


class CaseUpdate(Input):
    title: str | None = Field(default=None, min_length=1, max_length=250)
    description: str | None = Field(default=None, max_length=20000)
    expected_updated_at: datetime


class ClaimCreate(Input):
    statement: str = Field(min_length=1, max_length=20000)


class ClaimRead(ClaimCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    case_id: int
    status: str
    verdict: str


class EvidenceCreate(Input):
    title: str = Field(min_length=1, max_length=250)
    content: str = Field(min_length=1, max_length=100000)
    kind: Literal['document','image','video','audio','url','testimony']
    source_id: int | None = Field(default=None, gt=0)
    original_url: HttpUrl | None = Field(default=None, max_length=500)
    collected_at: datetime | None = None


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    case_id: int
    source_id: int | None
    title: str
    content: str
    kind: str
    original_url: str | None
    collected_at: datetime | None
    status: str


class EvidenceLinkCreate(Input):
    evidence_id: int = Field(gt=0)
    stance: Literal['supports','refutes','context'] = 'context'
    rationale: str = Field(default='', max_length=10000)


class EvidenceLinkRead(EvidenceLinkCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    claim_id: int
    status: str


class ManualDraftCreate(Input):
    signal_id: int = Field(gt=0)
    claim_id: int | None = Field(default=None, gt=0)
    titre_suggere: str = Field(min_length=1, max_length=250)
    synthese_ia: str = Field(min_length=1, max_length=100000)


class LocalResearchCreate(Input):
    question: str = Field(min_length=3, max_length=500)


class ResearchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    case_id: int | None
    sujet: str
    statut: str
    modele: str
    synthese: str | None
    citations: list[dict]
    erreurs: list[str]
    debut: datetime
    fin: datetime | None


class RevisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    draft_id: int
    actor_id: int
    version: int
    event: str
    snapshot: dict
    created_at: datetime
