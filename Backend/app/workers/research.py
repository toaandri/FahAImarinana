"""Callable research job with its own database session."""
from ..database import SessionLocal
from ..database.scope import set_scope
from ..core.config import get_settings
from ..services.research import build_research_answer


def run(question: str):
    with SessionLocal() as db:
        settings = get_settings()
        set_scope(db, settings.default_newsroom_id, settings.default_dataset)
        return build_research_answer(db, question)
