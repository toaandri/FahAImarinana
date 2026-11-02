from fastapi import APIRouter
from .endpoints import alert, auth, copilot, draft, health, public, signal, sms, source, workflow

api_router = APIRouter()
for module in (health, source, signal, draft, public, auth, workflow, sms, alert, copilot):
    api_router.include_router(module.router)
