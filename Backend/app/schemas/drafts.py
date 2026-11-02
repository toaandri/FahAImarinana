from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    signal_id: int
    titre_suggere: str
    synthese_ia: str
    score_credibilite_indicatif: float
    sources_croisees: list[dict[str, Any]]
    statut: str
    horodatage: datetime
