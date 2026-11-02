import logging
from hashlib import sha256
from sqlalchemy.orm import Session
from ..models import SignalBrut
from ..repositories import ContactRepository
logger = logging.getLogger(__name__)

def alert_journalists(db: Session, signal: SignalBrut, send_sms) -> list[str]:
    if not signal.est_urgent:
        return []
    contacts = ContactRepository(db).active()
    short_id = sha256(f"signal:{signal.id}".encode()).hexdigest()[:8].upper()
    message = f"ALERTE {short_id}: {signal.contenu_normalise[:120]}"
    sent = []
    for contact in contacts:
        send_sms(contact.numero_telephone, message)
        sent.append(contact.numero_telephone)
    return sent
