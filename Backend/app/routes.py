from fastapi import APIRouter

from .controllers.draft_controller import router as draft_router
from .controllers.health_controller import router as health_router
from .controllers.public_controller import router as public_router
from .controllers.signal_controller import router as signal_router
from .controllers.source_controller import router as source_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(source_router)
api_router.include_router(signal_router)
api_router.include_router(draft_router)
api_router.include_router(public_router)
