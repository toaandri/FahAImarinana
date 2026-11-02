"""Scoped investigation operations and explicit local documentary search."""
from datetime import timezone
import re
from sqlalchemy import select
from ..core.errors import NotFoundError, ConflictError
from ..core.rbac import Permission as P, authorize
from ..core.security import now
from ..database.scope import scope_for_user
from ..models import Case, Claim, Evidence, ClaimEvidence, Source, Signal, Draft, ResearchJob


def get_case(db, case_id, *, writable=False):
    statement = select(Case).where(Case.id == case_id)
    if writable:
        statement = statement.with_for_update().execution_options(populate_existing=True)
    case = db.scalar(statement)
    if case is None:
        raise NotFoundError('Dossier introuvable.')
    if writable and case.status == 'archived':
        raise ConflictError('Ce dossier est archivé.')
    return case


def update_case(db, user, case_id, payload):
    authorize(user, P.CASE_EDIT); scope_for_user(db, user)
    case = get_case(db, case_id, writable=True)
    def utc(value):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    if utc(case.updated_at) != utc(payload.expected_updated_at):
        raise ConflictError('Le dossier a changé ; recharger sa version.')
    for field, value in payload.model_dump(exclude={'expected_updated_at'}, exclude_none=True).items():
        setattr(case, field, value)
    db.commit()
    db.refresh(case)  # PostgreSQL's timestamp trigger is authoritative.
    return case


def add_claim(db, user, case_id, payload):
    authorize(user, P.CLAIM_ADD); scope_for_user(db, user)
    get_case(db, case_id, writable=True)
    claim = Claim(case_id=case_id, statement=payload.statement)
    db.add(claim); db.commit()
    return claim


def add_evidence(db, user, case_id, payload):
    authorize(user, P.EVIDENCE_ADD); scope_for_user(db, user)
    get_case(db, case_id, writable=True)
    if payload.source_id is not None and db.scalar(select(Source.id).where(Source.id == payload.source_id)) is None:
        raise NotFoundError('Source introuvable.')
    values = payload.model_dump(exclude={'original_url'})
    record = Evidence(case_id=case_id, **values,
        original_url=str(payload.original_url) if payload.original_url else None,
        confidentiality='confidential')
    if record.collected_at is None:
        record.collected_at = now()
    db.add(record); db.commit()
    return record


def link_evidence(db, user, case_id, claim_id, payload):
    authorize(user, P.EVIDENCE_ADD); scope_for_user(db, user)
    get_case(db, case_id, writable=True)
    if db.scalar(select(Claim.id).where(Claim.id == claim_id, Claim.case_id == case_id)) is None:
        raise NotFoundError('Affirmation introuvable dans ce dossier.')
    if db.scalar(select(Evidence.id).where(Evidence.id == payload.evidence_id, Evidence.case_id == case_id)) is None:
        raise NotFoundError('Preuve introuvable dans ce dossier.')
    if db.scalar(select(ClaimEvidence.id).where(ClaimEvidence.claim_id == claim_id, ClaimEvidence.evidence_id == payload.evidence_id)):
        raise ConflictError('Cette preuve est déjà associée à cette affirmation.')
    record = ClaimEvidence(case_id=case_id, claim_id=claim_id, **payload.model_dump())
    db.add(record); db.commit()
    return record


def create_manual_draft(db, user, case_id, payload):
    authorize(user, P.DRAFT_EDIT); scope_for_user(db, user)
    get_case(db, case_id, writable=True)
    signal = db.scalar(select(Signal).where(Signal.id == payload.signal_id, Signal.case_id == case_id))
    if signal is None:
        raise NotFoundError('Signal introuvable dans ce dossier.')
    if payload.claim_id is not None and db.scalar(select(Claim.id).where(Claim.id == payload.claim_id, Claim.case_id == case_id)) is None:
        raise NotFoundError('Affirmation introuvable dans ce dossier.')
    if db.scalar(select(Draft.id).where(Draft.signal_id == payload.signal_id)):
        raise ConflictError('Un brouillon existe déjà pour ce signal.')
    draft = Draft(case_id=case_id, **payload.model_dump(), score_credibilite_indicatif=0,
        sources_croisees=[], horodatage=now())
    db.add(draft); db.flush()
    from .draft_workflow import record_revision
    record_revision(db, draft, user.id, 'created')
    db.commit()
    return draft


def search_case_pieces(db,case_id,question):
    """Bounded CPU-only extraction, shared by HTTP and durable queue workers."""
    terms = list(dict.fromkeys(re.findall(r'\w{2,}',question.casefold())))[:30]
    pieces = list(db.scalars(select(Evidence).where(Evidence.case_id == case_id).order_by(Evidence.id).limit(1001)))
    truncated = len(pieces)>1000
    pieces = pieces[:1000]
    matches = []
    for piece in pieces:
        text = (piece.title + ' ' + piece.content).casefold()
        score = sum(text.count(term) for term in terms)
        if score:
            matches.append((score, piece))
    matches.sort(key=lambda pair: (-pair[0], pair[1].id))
    citations = [{'evidence_id': piece.id, 'source_id': piece.source_id, 'titre': piece.title,
                  'url': piece.original_url, 'extrait': piece.content[:1000]} for _, piece in matches[:20]]
    return {'requetes':terms,'citations':citations,'statut':'partielle' if truncated else 'terminee',
        'synthese':('Recherche lexicale locale : ' + str(len(citations)) + ' pièce(s) correspondante(s). '
            'Aucune recherche web ni analyse Maharavo effectuée. Les reprises d’une même source '
            'ne constituent pas des confirmations indépendantes. Validation humaine nécessaire.'),
        'erreurs':['Limite de 1000 pièces atteinte ; recherche partielle.'] if truncated else []}


def local_research(db, user, case_id, payload):
    """Search stored pieces only. No web access, truth judgment or generated facts."""
    authorize(user, P.RESEARCH_RUN); scope_for_user(db, user)
    get_case(db, case_id, writable=True)
    job = ResearchJob(utilisateur_id=user.id, case_id=case_id, sujet=payload.question,
        modele='local-document-search-v1', debut=now(), fin=now(), questions=[payload.question],
        **search_case_pieces(db,case_id,payload.question))
    db.add(job); db.commit()
    return job
