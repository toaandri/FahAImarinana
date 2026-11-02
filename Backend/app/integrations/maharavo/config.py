"""Transport configuration only: no undocumented endpoint or authentication scheme."""
from functools import lru_cache
import os
from typing import Annotated
from pydantic import BaseModel, Field, SecretStr, model_validator
from urllib.parse import urlsplit


class MaharavoSettings(BaseModel):
    enabled: bool = False
    base_url: str | None = None
    api_key: SecretStr = SecretStr('')
    allowed_model_versions: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(default_factory=list, max_length=20)
    connect_timeout: float = Field(default=10, gt=0, le=60)
    read_timeout: float = Field(default=30, gt=0, le=120)
    write_timeout: float = Field(default=10, gt=0, le=60)
    pool_timeout: float = Field(default=5, gt=0, le=60)
    total_timeout: float = Field(default=90, gt=0, le=300)
    max_attempts: int = Field(default=3, ge=1, le=5)
    backoff_seconds: float = Field(default=0.5, gt=0, le=10)
    max_backoff_seconds: float = Field(default=10, gt=0, le=60)
    requests_per_minute: int = Field(default=30, ge=1, le=600)
    max_concurrent_requests: int = Field(default=2, ge=1, le=20)
    max_request_bytes: int = Field(default=262144, ge=1024, le=2097152)
    max_response_bytes: int = Field(default=524288, ge=1024, le=4194304)
    max_sources: int = Field(default=10, ge=1, le=100)
    max_documents: int = Field(default=5, ge=1, le=50)
    max_evidence: int = Field(default=20, ge=1, le=200)
    max_claims: int = Field(default=50, ge=1, le=500)
    max_analysis_chars: int = Field(default=50000, ge=100, le=200000)
    max_draft_chars: int = Field(default=20000, ge=100, le=100000)
    max_quote_chars: int = Field(default=5000, ge=10, le=10000)
    clock_skew_seconds: int = Field(default=30, ge=0, le=120)

    @model_validator(mode='after')
    def validate_transport(self):
        if self.base_url:
            url = urlsplit(self.base_url)
            if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
                raise ValueError('MAHARAVO_BASE_URL doit être une URL HTTPS sans identifiants ni paramètres.')
        if self.enabled and (not self.base_url or not self.api_key.get_secret_value() or not self.allowed_model_versions):
            raise ValueError('URL, clé et versions de modèle explicites sont requises pour activer le transport.')
        if self.max_backoff_seconds < self.backoff_seconds:
            raise ValueError('Le plafond du backoff doit dépasser son délai initial.')
        return self


@lru_cache
def get_maharavo_settings():
    # Core configuration has already loaded Backend/.env at application startup.
    values = {key: os.environ['MAHARAVO_' + key.upper()] for key in MaharavoSettings.model_fields
              if 'MAHARAVO_' + key.upper() in os.environ}
    if 'allowed_model_versions' in values:
        values['allowed_model_versions'] = [value.strip() for value in values['allowed_model_versions'].split(',') if value.strip()]
    return MaharavoSettings.model_validate(values)
