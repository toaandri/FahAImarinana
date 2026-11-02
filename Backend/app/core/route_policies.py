"""Method/path policies shared by the authorization middleware and its coverage tests."""
import re
from .rbac import Permission as P

PUBLIC_ROUTES=frozenset({('GET','/health'),('GET','/public/articles'),('GET','/public/sync'),('POST','/sms/citizen'),
    ('POST','/auth/register'),('POST','/auth/login'),('POST','/auth/refresh'),('POST','/auth/service-token')})
# None means authentication only (own profile/session management).
POLICIES=[
    ('GET',r'/auth/me',None),('GET',r'/auth/sessions',None),('DELETE',r'/auth/sessions/[a-f0-9]{32}',None),
    ('POST',r'/auth/(logout|logout-all|password)',None),
    ('GET',r'/admin/users',P.USERS_MANAGE),('PATCH',r'/admin/users/[0-9]+',P.USERS_MANAGE),
    ('POST',r'/admin/(invitations|service-accounts)',P.USERS_MANAGE),
    ('GET',r'/admin/settings',P.SETTINGS_MANAGE),('PUT',r'/admin/settings/[a-z_]+',P.SETTINGS_MANAGE),
    ('GET',r'/sources',P.CONNECTORS_MANAGE),('POST',r'/sources',P.CONNECTORS_MANAGE),('PATCH',r'/sources/[0-9]+',P.CONNECTORS_MANAGE),
    ('GET',r'/cases(/[0-9]+)?',P.CASE_READ),('POST',r'/cases',P.CASE_CREATE),
    ('PATCH',r'/cases/[0-9]+',P.CASE_EDIT),
    ('POST',r'/cases/[0-9]+/archive',P.CASE_EDIT),
    ('GET',r'/cases/[0-9]+/(claims|evidence|sources|drafts|research)',P.CASE_READ),
    ('POST',r'/cases/[0-9]+/claims',P.CLAIM_ADD),
    ('POST',r'/cases/[0-9]+/claims/[0-9]+/evidence',P.EVIDENCE_ADD),
    ('GET',r'/cases/[0-9]+/claims/[0-9]+/evidence',P.CASE_READ),
    ('POST',r'/cases/[0-9]+/drafts',P.DRAFT_EDIT),
    ('POST',r'/cases/[0-9]+/research',P.RESEARCH_RUN),
    ('POST',r'/cases/[0-9]+/evidence',P.EVIDENCE_ADD),
    ('POST',r'/contributions/signals',P.CONTRIBUTION_ADD),
    ('POST',r'/contributions/[0-9]+/information',P.CONTRIBUTION_ADD),
    ('GET',r'/contributions/[0-9]+',P.CONTRIBUTION_ADD),
    ('POST',r'/signals/ingest',P.SIGNAL_INGEST),('POST',r'/signals/[0-9]+/analyze',P.DRAFT_CREATE),
    ('GET',r'/drafts/[0-9]+(/version)?',P.DRAFT_READ),('PATCH',r'/drafts/[0-9]+',P.DRAFT_EDIT),
    ('GET',r'/drafts/[0-9]+/history',P.DRAFT_READ),
    ('POST',r'/workflow/process-pending',P.TASKS_RUN),
    ('POST',r'/workflow/signals/[0-9]+/cross-check',P.RESEARCH_RUN),
    ('POST',r'/workflow/drafts/[0-9]+/review',P.DRAFT_REVIEW),
    ('POST',r'/workflow/drafts/[0-9]+/validate',P.VERSION_VALIDATE),
    ('POST',r'/workflow/drafts/[0-9]+/publish',P.PUBLISH),
    ('POST',r'/workflow/publications/[0-9]+/(correct|withdraw)',P.CORRECT),
    ('GET',r'/copilot/sessions(/[0-9]+/messages)?',P.RESEARCH_RUN),
    ('POST',r'/copilot/(sessions|sessions/[0-9]+/ask|research)',P.RESEARCH_RUN),
    ('POST',r'/copilot/index/articles',P.INDEX_WRITE),
    ('POST',r'/copilot/alerts/signal/[0-9]+',P.ALERTS_SEND),
    ('POST',r'/maharavo/research',P.RESEARCH_RUN),
    ('POST',r'/maharavo/(media-analysis|confidence)',P.ANALYSIS_WRITE),
]


def canonical_api_path(path):
    if path=='/api/v1' or path.startswith('/api/v1/'):
        return path[7:].rstrip('/') or '/'
    if path=='/api' or path.startswith('/api/'):
        return path[4:].rstrip('/') or '/'
    return None


def policy_for(method,path):
    for verb,pattern,permission in POLICIES:
        if method==verb and re.fullmatch(pattern,path):
            return True,permission
    return False,None
