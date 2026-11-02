from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import get_settings
from .database import Base, engine, public_engine
from .database.public import create_public_views, verify_public_role
from . import models  # register metadata before startup
from .api.v1.router import api_router
from .middleware.authorization import AuthorizationMiddleware
from .middleware.errors import register_error_handlers
from .middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI):
    if get_settings().auto_create_tables:
        Base.metadata.create_all(bind=engine)
        with engine.begin() as connection:
            from .database.bootstrap import bootstrap_newsrooms
            bootstrap_newsrooms(connection)
            from sqlalchemy import inspect
            if "public_publications" not in inspect(connection).get_view_names():
                create_public_views(connection)
            from .database.guards import install_guards
            install_guards(connection, Base.metadata.tables)
    if get_settings().environment == "production":
        with public_engine.connect() as connection:
            verify_public_role(connection)
    try:
        yield
    finally:
        engine.dispose()
        if public_engine is not engine:
            public_engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="FANILO Backend", version="1.0.0",
        description="API de veille et fact-checking avec validation humaine obligatoire.",
        lifespan=lifespan,
    )
    application.add_middleware(AuthorizationMiddleware)
    application.add_middleware(RateLimitMiddleware,auth_limit=settings.auth_requests_per_minute,
                               public_limit=settings.public_requests_per_minute)
    application.add_middleware(
        CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"], allow_headers=["*"],
    )
    register_error_handlers(application)
    application.include_router(api_router, prefix="/api/v1")
    application.include_router(api_router, prefix="/api", include_in_schema=False)
    return application


app = create_app()
