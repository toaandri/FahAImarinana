from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SignalIngest(BaseModel):
    source_id: int = Field(gt=0)
    contenu: str = Field(min_length=1, max_length=100_000)
    url_origine: HttpUrl = Field(max_length=500)
    horodatage_publication: datetime
    auteur: str | None = Field(default=None, max_length=150)
    nombre_interactions: int = Field(default=0, ge=0)


class SignalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    contenu_normalise: str
    niveau_viralite: float
    mots_cles_detectes: list[str]
    est_urgent: bool


class CrossCheckSource(BaseModel):
    titre: str = Field(min_length=1, max_length=250)
    url: HttpUrl = Field(max_length=500)
    extrait: str = Field(min_length=1, max_length=5_000)
    concorde: bool = True
    officielle: bool = False


class AnalyzeRequest(BaseModel):
    sources_croisees: list[CrossCheckSource] = Field(default_factory=list, max_length=20)


class CrossCheckRead(BaseModel):
    signal_id: int
    sources: list[CrossCheckSource]
    score_concordance: float
