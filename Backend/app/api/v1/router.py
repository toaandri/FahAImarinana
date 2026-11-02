from fastapi import APIRouter
from .endpoints import alert, auth, copilot, draft, health, public, signal, sms, source, workflow, maharavo, admin, investigations

api_router = APIRouter()
for module in (health, source, signal, draft, public, auth, workflow, sms, alert, copilot, maharavo, admin, investigations):
    api_router.include_router(module.router)
