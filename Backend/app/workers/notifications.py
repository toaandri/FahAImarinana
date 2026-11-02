"""Notification job; gateway is injectable, simulation is the default."""
from ..database import SessionLocal
from ..core.errors import NotFoundError
from ..repositories import SignalRepository
from ..services.notifications import alert_journalists
from ..integrations.sms.gateway import SimulationSmsGateway, SmsGateway


def run(signal_id: int, gateway: SmsGateway | None = None):
    with SessionLocal() as db:
        signal = SignalRepository(db).get(signal_id)
        if signal is None:
            raise NotFoundError("Signal introuvable.")
        return alert_journalists(db, signal, (gateway or SimulationSmsGateway()).send)
