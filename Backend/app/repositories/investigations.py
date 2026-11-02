"""Scoped CRUD repositories; the session enforces newsroom/dataset on every query."""
from .base import Repository
from ..models import Case, Claim, Evidence, ClaimEvidence, ResearchJob, MediaAnalysis, CorrectionAudit, SmsExchange


class CaseRepository(Repository[Case]):
    model = Case


class ClaimRepository(Repository[Claim]):
    model = Claim


class EvidenceRepository(Repository[Evidence]):
    model = Evidence


class ClaimEvidenceRepository(Repository[ClaimEvidence]):
    model = ClaimEvidence


class ResearchJobRepository(Repository[ResearchJob]):
    model = ResearchJob


class MediaAnalysisRepository(Repository[MediaAnalysis]):
    model = MediaAnalysis


class CorrectionAuditRepository(Repository[CorrectionAudit]):
    model = CorrectionAudit


class SmsExchangeRepository(Repository[SmsExchange]):
    model = SmsExchange
