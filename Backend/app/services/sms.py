from ..core.constants import SECURITY_RESPONSE
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models import HistoriqueSms
from ..repositories import ArticleRepository
from ..utils.text import normalize_text
logger = logging.getLogger(__name__)

def answer_citizen_sms(db: Session, payload) -> tuple[str, str]:
    query = normalize_text(payload.message)
    words = [word for word in query.casefold().split() if len(word) >= 4][:8]
    articles = ArticleRepository(db).matching(words, 1)
    if articles:
        response, status = articles[0].contenu_optimise_sms, "Trouve"
    else:
        response, status = SECURITY_RESPONSE, "Non_Trouve"
    db.add(HistoriqueSms(
        numero_expediteur=payload.numero_expediteur,
        message_recu=payload.message,
        message_envoye=response,
        horodatage=datetime.now(timezone.utc),
        statut_reponse=status,
    ))
    db.commit()
    return response, status
