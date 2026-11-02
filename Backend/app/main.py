import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .controllers.draft_controller import router as draft_router
from .controllers.health_controller import router as health_router
from .controllers.public_controller import router as public_router
from .controllers.signal_controller import router as signal_router
from .controllers.source_controller import router as source_router
from .controllers.alert_controller import router as alert_router
from .controllers.auth_controller import router as auth_router
from .controllers.copilot_controller import router as copilot_router
from .controllers.sms_controller import router as sms_router
from .controllers.workflow_controller import router as workflow_router
from .controllers.maharavo_controller import router as maharavo_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    if os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true":
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="FANILO Backend",
    description="API MVC de veille et fact-checking avec validation humaine obligatoire.",
    lifespan=lifespan,
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://localhost:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
for router in (
    health_router,
    source_router,
    signal_router,
    draft_router,
    public_router,
    auth_router,
    workflow_router,
    sms_router,
    alert_router,
    copilot_router,
    maharavo_router,
):
    app.include_router(router, prefix="/api")
