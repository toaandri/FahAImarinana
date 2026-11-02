from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SourceCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=150)
    type: Literal["Facebook", "X", "Web", "RSS"]
    url: HttpUrl = Field(max_length=500)
    frequence_scan_secondes: int = Field(default=900, ge=60)


class SourceRead(SourceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    statut: str
    derniere_verification: datetime | None = None
