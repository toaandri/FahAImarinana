"""Explicit grants for human journalists and scoped technical identities."""
from enum import StrEnum
from .errors import ForbiddenError


class Role(StrEnum):
    JOURNALISTE = 'JOURNALISTE'
    SERVICE_IA = 'SERVICE_IA'


class Permission(StrEnum):
    CASE_READ = 'cases.read'
    CASE_CREATE = 'cases.create'
    CASE_EDIT = 'cases.edit'
    CLAIM_ADD = 'claims.add'
    EVIDENCE_ADD = 'evidence.add'
    SIGNAL_INGEST = 'signals.ingest'
    CONTRIBUTION_ADD = 'contributions.add'
    RESEARCH_RUN = 'research.run'
    ANALYSIS_WRITE = 'analyses.write'
    DRAFT_READ = 'drafts.read'
    DRAFT_CREATE = 'drafts.create'
    DRAFT_EDIT = 'drafts.edit'
    DRAFT_REVIEW = 'drafts.review'
    VERSION_VALIDATE = 'versions.validate'
    PUBLISH = 'publications.publish'
    CORRECT = 'publications.correct'
    USERS_MANAGE = 'users.manage'
    CONNECTORS_MANAGE = 'connectors.manage'
    SETTINGS_MANAGE = 'settings.manage'
    TASKS_RUN = 'tasks.run'
    ALERTS_READ = 'alerts.read'
    ALERTS_SEND = 'alerts.send'
    INDEX_WRITE = 'index.write'


P = Permission
ROLE_PERMISSIONS = {
    Role.JOURNALISTE: frozenset({
        P.CASE_READ, P.CASE_CREATE, P.CASE_EDIT, P.CLAIM_ADD, P.EVIDENCE_ADD,
        P.SIGNAL_INGEST, P.CONTRIBUTION_ADD, P.RESEARCH_RUN, P.ANALYSIS_WRITE,
        P.DRAFT_READ, P.DRAFT_CREATE, P.DRAFT_EDIT, P.DRAFT_REVIEW,
        P.VERSION_VALIDATE, P.PUBLISH, P.CORRECT, P.USERS_MANAGE,
        P.CONNECTORS_MANAGE, P.SETTINGS_MANAGE, P.ALERTS_READ, P.ALERTS_SEND,
        P.INDEX_WRITE,
    }),
    Role.SERVICE_IA: frozenset({P.RESEARCH_RUN,P.ANALYSIS_WRITE,P.DRAFT_CREATE,P.TASKS_RUN}),
}


def canonical_role(value: str) -> str:
    value = {
        'Journaliste': 'JOURNALISTE',
        'Editeur': 'JOURNALISTE',
        'EDITEUR': 'JOURNALISTE',
        'ADMINISTRATEUR': 'JOURNALISTE',
        'CONTRIBUTEUR': 'JOURNALISTE',
        'LECTEUR': 'JOURNALISTE',
    }.get(value, value)
    return Role(value).value


def permissions_for(user) -> frozenset:
    try:
        role = Role(canonical_role(user.role))
    except (ValueError,TypeError):
        return frozenset()
    grants = ROLE_PERMISSIONS[role]
    if role == Role.SERVICE_IA:
        grants = grants.intersection(user.service_permissions or [])
    return grants


def authorize(user, permission: Permission):
    if not user.actif or user.status != 'active' or permission not in permissions_for(user):
        raise ForbiddenError('Permission insuffisante.')
    # A service identity is permanently excluded, even after a role/configuration mistake.
    if user.account_type == 'service' and permission in {P.VERSION_VALIDATE,P.PUBLISH,P.CORRECT,P.DRAFT_REVIEW}:
        raise ForbiddenError('Une identité IA ne peut pas prendre de décision éditoriale.')
    return user
