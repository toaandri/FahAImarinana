from datetime import datetime, timezone, timedelta
from pydantic import ValidationError
from .config import MaharavoSettings
from .contracts import TaskRequest, TaskResponse
from .errors import MaharavoProtocolError, MaharavoLimitError
from .provenance import ConsultationManifest


def invalid():
    raise MaharavoProtocolError('Réponse Maharavo non conforme ou références documentaires non justifiées.')


def validate_request(request: TaskRequest, manifest: ConsultationManifest, settings: MaharavoSettings):
    if request.model_version not in settings.allowed_model_versions:
        invalid()
    if request.task_id != manifest.task_id or len(request.documents) > settings.max_documents:
        invalid()
    if tuple(request.documents) != manifest.documents:
        invalid()


def validate_response(candidate, request: TaskRequest, manifest: ConsultationManifest,
                      settings: MaharavoSettings, *, now=None) -> TaskResponse:
    try:
        result = TaskResponse.model_validate(candidate)
    except (ValidationError, TypeError, ValueError):
        invalid()
    validate_request(request, manifest, settings)
    now = now or datetime.now(timezone.utc)
    tolerance = timedelta(seconds=settings.clock_skew_seconds)
    if (result.task_id != request.task_id or result.task_type != request.task_type
        or result.model_version != request.model_version
        or result.model_version not in settings.allowed_model_versions
        or result.generated_at > now + tolerance or result.generated_at < request.submitted_at - tolerance):
        invalid()
    if (len(result.sources) > settings.max_sources or len(result.sources) > settings.max_documents
        or len(result.evidence) > settings.max_evidence):
        raise MaharavoLimitError('Le résultat dépasse les limites documentaires configurées.')
    documents = manifest.by_id
    sources = {}
    for source in result.sources:
        snapshot = documents.get(source.document_id)
        if snapshot is None or source.document_id in sources:
            invalid()
        if (source.consultation_id != snapshot.consultation_id or source.url != snapshot.url
            or source.sha256 != snapshot.sha256 or source.consulted_at != snapshot.consulted_at
            or source.consulted_at > result.generated_at + tolerance):
            invalid()
        sources[source.document_id] = source
    evidence = {}
    covered_sources = set()
    for item in result.evidence:
        snapshot = documents.get(item.document_id)
        if (snapshot is None or item.document_id not in sources or item.evidence_id in evidence
            or item.consultation_id != snapshot.consultation_id or not item.quote.strip()
            or item.quote not in snapshot.text):
            invalid()
        if len(item.quote) > settings.max_quote_chars:
            raise MaharavoLimitError('Un extrait dépasse la longueur configurée.')
        evidence[item.evidence_id] = item
        covered_sources.add(item.document_id)
    if covered_sources != set(sources):
        invalid()
    analysis = result.analysis
    if analysis is None:
        return result

    def check_refs(references):
        if len(references) != len(set(references)) or any(ref not in evidence for ref in references):
            invalid()

    check_refs(analysis.summary_evidence_ids)
    if analysis.summary and not analysis.summary_evidence_ids:
        invalid()
    if len(analysis.claims) > settings.max_claims:
        raise MaharavoLimitError('Trop d’affirmations proposées.')
    if len({claim.claim_id for claim in analysis.claims}) != len(analysis.claims):
        invalid()
    for claim in analysis.claims:
        check_refs(claim.evidence_ids)
    for item in analysis.documents:
        check_refs(item.evidence_ids)
        if item.document_id not in sources or any(evidence[ref].document_id != item.document_id for ref in item.evidence_ids):
            invalid()
    for match in analysis.source_matches:
        check_refs(match.evidence_ids)
        if (len(match.document_ids) != len(set(match.document_ids))
            or not set(match.document_ids) <= set(sources)
            or set(match.document_ids) != {evidence[ref].document_id for ref in match.evidence_ids}):
            invalid()
    for contradiction in analysis.contradictions:
        check_refs(contradiction.evidence_ids)
    if analysis.draft:
        check_refs(analysis.draft.evidence_ids)
        if len(analysis.draft.body) > settings.max_draft_chars:
            raise MaharavoLimitError('Le brouillon dépasse la longueur configurée.')
    text_size = len(analysis.summary or '') + sum(len(c.statement) for c in analysis.claims)
    text_size += sum(len(c.statement) for c in analysis.contradictions)
    text_size += sum(len(c.summary) for c in analysis.documents) + sum(len(c.explanation) for c in analysis.source_matches)
    if text_size > settings.max_analysis_chars:
        raise MaharavoLimitError('L’analyse dépasse la longueur configurée.')
    return result
