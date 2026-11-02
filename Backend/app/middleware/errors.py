import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from ..core.errors import DomainError

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error(_: Request, exc: DomainError):
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

    @app.exception_handler(IntegrityError)
    async def integrity_error(_: Request, exc: IntegrityError):
        # Do not return database statements or parameters to clients or logs.
        logger.warning("Database integrity conflict (%s)", type(exc).__name__)
        return JSONResponse(status_code=409, content={"detail": "Conflit avec les données existantes."})

    @app.exception_handler(SQLAlchemyError)
    async def database_error(_: Request, exc: SQLAlchemyError):
        logger.error("Database unavailable (%s)", type(exc).__name__)
        return JSONResponse(status_code=503, content={"detail": "Base de données temporairement indisponible."})

    @app.exception_handler(Exception)
    async def unexpected_error(_: Request, exc: Exception):
        logger.error("Unexpected server error (%s)", type(exc).__name__)
        return JSONResponse(status_code=500, content={"detail": "Erreur interne du serveur."})
