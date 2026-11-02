"""Notification job; gateway is injectable, simulation is the default."""
from ..database import SessionLocal
from ..database.scope import set_scope
from ..core.config import get_settings
from ..core.errors import NotFoundError
from ..repositories import SignalRepository
from ..services.notifications import alert_journalists
from ..integrations.sms.gateway import SimulationSmsGateway, SmsGateway


def run(signal_id: int, gateway: SmsGateway | None = None):
    with SessionLocal() as db:
        settings = get_settings()
        set_scope(db, settings.default_newsroom_id, settings.default_dataset)
        signal = SignalRepository(db).get(signal_id)
        if signal is None:
            raise NotFoundError("Signal introuvable.")
        return alert_journalists(db, signal, (gateway or SimulationSmsGateway()).send)
