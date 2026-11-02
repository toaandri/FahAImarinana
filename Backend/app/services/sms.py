from ..core.constants import SECURITY_RESPONSE
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models import HistoriqueSms
from ..repositories.publications import PublicPublicationRepository
from ..core.config import get_settings
from ..database.scope import set_scope
from ..utils.text import normalize_text
logger = logging.getLogger(__name__)

def answer_citizen_sms(db: Session, payload, *, public_db: Session | None = None) -> tuple[str, str]:
    settings = get_settings()
    set_scope(db, settings.public_newsroom_id, settings.public_dataset)
    query = normalize_text(payload.message)
    import re
    words = re.findall(r'\w{2,}',query.casefold())[:8]
    articles = PublicPublicationRepository(public_db or db).matching(words, 1)
    if articles:
        response, status = articles[0]["contenu_optimise_sms"], "Trouve"
    else:
        response, status = SECURITY_RESPONSE, "Non_Trouve"
    db.add(HistoriqueSms(
        publication_id=articles[0]["id"] if articles else None,
        numero_expediteur=payload.numero_expediteur,
        message_recu=payload.message,
        message_envoye=response,
        horodatage=datetime.now(timezone.utc),
        statut_reponse=status,
    ))
    db.commit()
    return response, status
