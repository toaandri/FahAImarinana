from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import get_settings
from .database import Base, engine
from . import models  # register metadata before startup
from .api.v1.router import api_router
from .middleware.errors import register_error_handlers


@asynccontextmanager
async def lifespan(_: FastAPI):
    if get_settings().auto_create_tables:
        Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="FANILO Backend", version="1.0.0",
        description="API de veille et fact-checking avec validation humaine obligatoire.",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"],
    )
    register_error_handlers(application)
    application.include_router(api_router, prefix="/api/v1")
    application.include_router(api_router, prefix="/api", include_in_schema=False)
    return application


app = create_app()
