"""PROPOSED backend-normalized contract. Not a claim about a remote Maharavo API."""
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, model_validator, field_validator

Text = Annotated[str, Field(min_length=1, max_length=100000)]
Identifier = Annotated[str, Field(min_length=1, max_length=100)]
Digest = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
Refs = Annotated[list[Identifier], Field(min_length=1, max_length=200)]


class TaskType(StrEnum):
    RESEARCH = 'research'
    DOCUMENT_ANALYSIS = 'document_analysis'
    CLAIM_EXTRACTION = 'claim_extraction'
    SOURCE_MATCHING = 'source_matching'
    CONTRADICTION_ANALYSIS = 'contradiction_analysis'
    SYNTHESIS = 'synthesis'
    DRAFT_PREPARATION = 'draft_preparation'


TASK_SPACES = {kind: ('research' if kind == TaskType.RESEARCH else
                     'drafts' if kind == TaskType.DRAFT_PREPARATION else 'analysis') for kind in TaskType}


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, allow_inf_nan=False)

    @field_validator('*')
    @classmethod
    def reject_blank_text(cls, value):
        if isinstance(value, str) and not value.strip():
            raise ValueError('Les chaînes blanches ne constituent pas un résultat.')
        return value


class DocumentInput(Contract):
    document_id: UUID
    consultation_id: UUID
    url: HttpUrl
    sha256: Digest
    consulted_at: AwareDatetime
    text: Text


class TaskRequest(Contract):
    contract_version: Literal['fa-ai-marinana.proposal.v1'] = 'fa-ai-marinana.proposal.v1'
    task_id: UUID
    task_type: TaskType
    model_version: Identifier
    submitted_at: AwareDatetime
    instructions: Annotated[str, Field(min_length=3, max_length=20000)]
    documents: Annotated[list[DocumentInput], Field(max_length=50)]


class SourceReference(Contract):
    document_id: UUID
    consultation_id: UUID
    url: HttpUrl
    sha256: Digest
    consulted_at: AwareDatetime


class EvidenceReference(Contract):
    evidence_id: Identifier
    document_id: UUID
    consultation_id: UUID
    quote: Annotated[str, Field(min_length=1, max_length=10000)]


class ClaimSuggestion(Contract):
    claim_id: Identifier
    statement: Annotated[str, Field(min_length=1, max_length=5000)]
    evidence_ids: Refs


class SourceMatch(Contract):
    document_ids: Annotated[list[UUID], Field(min_length=2, max_length=50)]
    explanation: Annotated[str, Field(min_length=1, max_length=5000)]
    evidence_ids: Refs


class Contradiction(Contract):
    statement: Annotated[str, Field(min_length=1, max_length=5000)]
    evidence_ids: Annotated[list[Identifier], Field(min_length=2, max_length=200)]


class DocumentAnalysis(Contract):
    document_id: UUID
    summary: Annotated[str, Field(min_length=1, max_length=20000)]
    evidence_ids: Refs


class DraftProposal(Contract):
    title: Annotated[str, Field(min_length=1, max_length=250)]
    body: Text
    language: Literal['fr', 'mg', 'en']
    evidence_ids: Refs


class Analysis(Contract):
    summary: Text | None = None
    summary_evidence_ids: Annotated[list[Identifier], Field(max_length=200)] = Field(default_factory=list)
    documents: Annotated[list[DocumentAnalysis], Field(max_length=50)] = Field(default_factory=list)
    claims: Annotated[list[ClaimSuggestion], Field(max_length=500)] = Field(default_factory=list)
    source_matches: Annotated[list[SourceMatch], Field(max_length=200)] = Field(default_factory=list)
    contradictions: Annotated[list[Contradiction], Field(max_length=200)] = Field(default_factory=list)
    draft: DraftProposal | None = None


class TaskError(Contract):
    code: Annotated[str, Field(pattern=r'^[a-z0-9_]{1,80}$')]
    message: Annotated[str, Field(min_length=1, max_length=2000)]


class TaskResponse(Contract):
    contract_version: Literal['fa-ai-marinana.proposal.v1']
    task_id: UUID
    task_type: TaskType
    status: Literal['completed', 'partial', 'failed']
    model_version: Identifier
    generated_at: AwareDatetime
    space: Literal['research', 'analysis', 'drafts']
    sources: Annotated[list[SourceReference], Field(max_length=100)]
    evidence: Annotated[list[EvidenceReference], Field(max_length=200)]
    analysis: Analysis | None
    limitations: Annotated[list[Annotated[str, Field(min_length=1, max_length=2000)]], Field(min_length=1, max_length=50)]
    errors: Annotated[list[TaskError], Field(max_length=50)]

    @field_validator('limitations')
    @classmethod
    def reject_blank_limitations(cls, value):
        if any(not item.strip() for item in value):
            raise ValueError('Les limites doivent être explicites.')
        return value

    @model_validator(mode='after')
    def result_shape(self):
        if self.space != TASK_SPACES[self.task_type]:
            raise ValueError('Espace de sortie interdit pour cette tâche.')
        if self.status == 'failed':
            if not self.errors or self.analysis is not None:
                raise ValueError('Un échec exige des erreurs et aucune analyse utilisable.')
            return self
        if not self.analysis or not self.sources or not self.evidence:
            raise ValueError('Une analyse utilisable exige des références documentaires.')
        if self.status == 'completed' and self.errors:
            raise ValueError('Un résultat complet ne doit pas masquer une erreur.')
        if self.status == 'partial' and not self.errors:
            raise ValueError('Un résultat partiel doit expliquer son échec partiel.')
        analysis = self.analysis
        required = {
            TaskType.RESEARCH: bool(analysis.summary and analysis.summary_evidence_ids),
            TaskType.DOCUMENT_ANALYSIS: bool(analysis.documents),
            TaskType.CLAIM_EXTRACTION: bool(analysis.claims),
            TaskType.SOURCE_MATCHING: bool(analysis.source_matches),
            TaskType.CONTRADICTION_ANALYSIS: bool(analysis.summary and analysis.summary_evidence_ids),
            TaskType.SYNTHESIS: bool(analysis.summary and analysis.summary_evidence_ids),
            TaskType.DRAFT_PREPARATION: bool(analysis.draft),
        }
        if not required[self.task_type]:
            raise ValueError('Contenu manquant pour ce type de tâche.')
        if analysis.draft is not None and self.space != 'drafts':
            raise ValueError('Un brouillon ne peut pas être écrit dans cet espace.')
        return self
