"""Callable research job with its own database session."""
from ..database import SessionLocal
from ..services.research import build_research_answer


def run(question: str):
    with SessionLocal() as db:
        return build_research_answer(db, question)
