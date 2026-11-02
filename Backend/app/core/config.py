"""Validated environment configuration, loaded once per process."""
import logging
import os
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr, model_validator
from sqlalchemy.engine import URL


class Settings(BaseModel):
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = ""
    public_database_url: str = ""
    default_newsroom_id: int = Field(default=1, gt=0)
    default_dataset: Literal["real", "demo", "quarantine"] = "real"
    public_newsroom_id: int = Field(default=1, gt=0)
    public_dataset: Literal["real", "demo"] = "real"
    database_host: str = "localhost"
    database_port: int = Field(default=5432, ge=1, le=65535)
    database_name: str = "fanilo"
    database_user: str = "fanilo"
    database_password: SecretStr = SecretStr("fanilo")
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=10, ge=0)
    auto_create_tables: bool = False
    jwt_secret: SecretStr = SecretStr("")
    jwt_expire_minutes: int = Field(default=15, ge=1)
    jwt_issuer: str = 'fa-ai-marinana'
    jwt_audience: str = 'fa-ai-marinana-api'
    refresh_expire_days: int = Field(default=30,ge=1,le=90)
    invitation_expire_hours: int = Field(default=48,ge=1,le=168)
    allow_public_registration: bool = False
    frontend_origins: str = "http://localhost:3000,http://localhost:5173"
    gemini_api_key: SecretStr = SecretStr("")
    gemini_model: str = "gemini-3.8-flash"
    gemini_timeout_seconds: float = Field(default=45, gt=0, le=300)
    sms_backend: Literal["simulation"] = "simulation"
    auth_requests_per_minute: int = Field(default=60,ge=1,le=10000)
    public_requests_per_minute: int = Field(default=60,ge=1,le=10000)

    @model_validator(mode="after")
    def validate_security(self):
        secret = self.jwt_secret.get_secret_value()
        if self.environment == "production":
            if len(secret.encode()) < 32 or secret == "change-me-in-production":
                raise ValueError("JWT_SECRET doit contenir au moins 32 octets en production.")
            if self.auto_create_tables:
                raise ValueError("Utiliser Alembic en production, pas AUTO_CREATE_TABLES.")
            if not self.public_database_url:
                raise ValueError("PUBLIC_DATABASE_URL est obligatoire en production.")
            from sqlalchemy.engine import make_url
            public_url = make_url(self.public_database_url)
            private_url = make_url(self.sqlalchemy_url)
            if public_url.get_backend_name() != "postgresql" or public_url.username == private_url.username:
                raise ValueError("Utiliser un compte PostgreSQL public distinct du compte applicatif.")
            if self.public_dataset != "real":
                raise ValueError("Le flux public de production doit servir les données réelles.")
            if self.allow_public_registration:
                raise ValueError("Désactiver ALLOW_PUBLIC_REGISTRATION en production.")
        elif not secret or secret == "change-me-in-production":
            self.jwt_secret = SecretStr(secrets.token_urlsafe(48))
            logging.getLogger(__name__).warning(
                "JWT_SECRET absent : secret temporaire de développement, jetons invalidés au redémarrage."
            )
        return self

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        return URL.create(
            "postgresql+psycopg", username=self.database_user,
            password=self.database_password.get_secret_value(), host=self.database_host,
            port=self.database_port, database=self.database_name,
        ).render_as_string(hide_password=False)

    @property
    def allowed_origins(self) -> list[str]:
        return [value.strip() for value in self.frontend_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    # Environment variables always take precedence over the local .env file.
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
    values = {name: os.environ[name.upper()] for name in Settings.model_fields if name.upper() in os.environ}
    if values.get("environment") == "production" and "allow_public_registration" not in values:
        values["allow_public_registration"] = False
    return Settings.model_validate(values)
