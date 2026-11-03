"""Read-only publication surface for an independently hosted public site."""
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from fastapi import FastAPI

from .api.v1.endpoints.public import public_article, public_sitemap
from .core.config import get_settings
from .database import public_engine
from .database.public import verify_public_role


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    if settings.environment != 'production':
        raise RuntimeError('Le site public hébergé exige ENVIRONMENT=production.')
    url = urlsplit(settings.public_site_url)
    if (url.scheme != 'https' or not url.hostname or url.username or url.password
        or url.query or url.fragment):
        raise RuntimeError('PUBLIC_SITE_URL doit être une adresse HTTPS publique.')
    with public_engine.connect() as connection:
        verify_public_role(connection)
    try:
        yield
    finally:
        public_engine.dispose()


app = FastAPI(title='FahAImarinana — articles publics', lifespan=lifespan,
              docs_url=None, redoc_url=None, openapi_url=None)
app.add_api_route('/api/v1/public/article', public_article, methods=['GET'])
app.add_api_route('/api/v1/public/sitemap.xml', public_sitemap, methods=['GET'])
