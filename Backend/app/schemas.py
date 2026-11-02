from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SourceCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=150)
    type: Literal["Facebook", "X", "Web", "RSS"]
    url: HttpUrl
    frequence_scan_secondes: int = Field(default=900, ge=60)


class SourceRead(SourceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    statut: str
    derniere_verification: datetime | None = None


class SignalIngest(BaseModel):
    source_id: int
    contenu: str = Field(min_length=1, max_length=100_000)
    url_origine: HttpUrl
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
    url: HttpUrl
    extrait: str = Field(min_length=1, max_length=5_000)
    concorde: bool = True
    officielle: bool = False


class AnalyzeRequest(BaseModel):
    sources_croisees: list[CrossCheckSource] = Field(default_factory=list, max_length=20)


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


class ArticlePublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titre_final: str
    corps_article: str
    categorie: str
    statut_verification: str
    horodatage_validation: datetime
    contenu_optimise_sms: str


class UserCreate(BaseModel):
    email: str
    mot_de_passe: str = Field(min_length=8)
    role: Literal["Journaliste", "Editeur"] = "Journaliste"


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PublishRequest(BaseModel):
    titre_final: str = Field(min_length=1, max_length=250)
    corps_article: str = Field(min_length=1)
    categorie: str = Field(min_length=1, max_length=50)
    statut_verification: Literal["Vrai", "Faux", "Trompeur"]
    contenu_optimise_sms: str = Field(min_length=1, max_length=480)


class SmsRequest(BaseModel):
    numero_expediteur: str = Field(min_length=5, max_length=30)
    message: str = Field(min_length=1, max_length=500)


class SmsResponse(BaseModel):
    message: str
    statut: str


class ResearchRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2_000)


class CrossCheckRead(BaseModel):
    signal_id: int
    sources: list[CrossCheckSource]
    score_concordance: float
