"""Backend injection boundary, unavailable until the real external adapter is documented."""
from typing import Protocol
from .contracts import TaskRequest, TaskResponse
from .provenance import ConsultationManifest
from .errors import MaharavoNotConfigured


class ResearchProvider(Protocol):
    async def execute(self, request: TaskRequest, manifest: ConsultationManifest) -> TaskResponse: ...


def get_research_provider() -> ResearchProvider:
    # A concrete vendor adapter cannot be inferred from the backend's own API routes.
    raise MaharavoNotConfigured()
