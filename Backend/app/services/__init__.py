"""Compatibility facade; implementations are separated by business domain."""
from .signals import ingest_signal, cross_check_signal
from .drafts import create_draft
from .editorial import publish_draft
from .sms import answer_citizen_sms
from .notifications import alert_journalists
from .research import index_certified_article, search_knowledge_base, build_research_answer
from .chat import create_chat_session, list_chat_sessions, get_chat_messages, ask_copilot
from ..core.security import authenticate_token, create_access_token, password_hash, password_matches
from ..integrations.sms.gateway import send_sms_via_gateway
from ..utils.text import normalize_text
