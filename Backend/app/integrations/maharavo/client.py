"""Connector host. There is deliberately no fabricated concrete Maharavo adapter."""
import logging
from .binding import DocumentedAdapter
from .config import MaharavoSettings
from .contracts import TaskRequest
from .errors import MaharavoNotConfigured, MaharavoProtocolError, MaharavoError
from .provenance import ConsultationManifest
from .transport import AsyncHTTPTransport
from .validation import validate_request, validate_response

logger = logging.getLogger(__name__)


class MaharavoClient:
    def __init__(self, settings: MaharavoSettings, *, adapter: DocumentedAdapter | None = None, transport=None):
        self.settings = settings
        self.adapter = adapter
        self.transport = transport or AsyncHTTPTransport(settings)

    def require_documented_interface(self):
        if (not self.settings.enabled or self.adapter is None
            or not self.adapter.documentation_reference.strip() or not self.adapter.api_version.strip()):
            raise MaharavoNotConfigured()

    async def execute(self, request: TaskRequest, manifest: ConsultationManifest):
        self.require_documented_interface()
        validate_request(request, manifest, self.settings)
        metadata = {'task_id': str(request.task_id), 'task_type': request.task_type.value,
                    'model_version': request.model_version, 'api_version': self.adapter.api_version}
        try:
            wire = self.adapter.encode(request, self.settings.api_key)
            raw = await self.transport.send(wire, task_id=request.task_id, task_type=request.task_type.value,
                model_version=request.model_version, api_version=self.adapter.api_version)
            try:
                normalized = self.adapter.normalize(raw)
            except (KeyError, TypeError, ValueError):
                raise MaharavoProtocolError('Réponse IA impossible à normaliser selon le contrat documenté.') from None
            result = validate_response(normalized, request, manifest, self.settings)
            logger.info('Maharavo result validated', extra={**metadata, 'task_status': result.status,
                        'source_count': len(result.sources), 'evidence_count': len(result.evidence)})
            return result
        except MaharavoError as exc:
            logger.warning('Maharavo result rejected', extra={**metadata, 'error_code': exc.code})
            raise

    async def aclose(self):
        await self.transport.aclose()
