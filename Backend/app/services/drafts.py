import logging
import re
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..database.scope import scope_for_user, set_scope
from ..models import DraftIA, SignalBrut
from ..core.errors import ConflictError
from ..repositories import DraftRepository
logger = logging.getLogger(__name__)
from ..integrations.ai.gemini import GeminiUnavailableError, generate_draft

def create_draft(db: Session, signal: SignalBrut, sources: list[dict]) -> DraftIA:
    set_scope(db, signal.newsroom_id, signal.dataset)
    if DraftRepository(db).by_signal(signal.id) is not None:
        raise ConflictError("Un brouillon existe déjà pour ce signal.")
    concordant = sum(1 for source in sources if source["concorde"])
    official = sum(1 for source in sources if source["officielle"])
    total = len(sources)
    score = 20.0 if not total else min(95.0, 35 + concordant / total * 45 + official * 10)
    try:
        generated = generate_draft(
            signal.contenu_normalise,
            signal.horodatage_publication.isoformat(),
            sources,
        )
        title = str(generated["titre"])[:250]
        summary = (
            f"{generated['synthese']}\n\nLimites: {generated['limites']} "
            "Cette synthèse est une pré-analyse IA et doit être relue par un journaliste."
        )
        score = max(0.0, min(100.0, float(generated["score_credibilite"])))
        if generated.get("citations"):
            sources = [*sources, *generated["citations"]]
    except (GeminiUnavailableError, KeyError, TypeError, ValueError):
        logger.info("Draft generation uses local fallback")
        first_sentence = re.split(r"(?<=[.!?])\s+", signal.contenu_normalise)[0]
        title = first_sentence[:247] + "..." if len(first_sentence) > 250 else first_sentence
        summary = (
            f"Signal détecté le {signal.horodatage_publication.isoformat()}. "
            f"{signal.contenu_normalise} "
            "Cette synthèse locale est une pré-analyse IA et doit être relue par un journaliste."
        )
    draft = DraftIA(
        signal_id=signal.id, case_id=signal.case_id,
        titre_suggere=title or "Signal sans titre",
        synthese_ia=summary,
        score_credibilite_indicatif=round(score, 2),
        sources_croisees=sources,
        statut="En_Attente",
        horodatage=datetime.now(timezone.utc),
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft
