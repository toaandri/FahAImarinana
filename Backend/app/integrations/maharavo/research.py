"""Research provider contract; the current implementation delegates to Gemini."""
from typing import Protocol
from ..ai.gemini import research_web


class ResearchProvider(Protocol):
    def research(self, question: str) -> tuple[str, list[dict]]: ...


class GeminiResearchProvider:
    def research(self, question: str) -> tuple[str, list[dict]]:
        return research_web(question)


def get_research_provider() -> ResearchProvider:
    return GeminiResearchProvider()
