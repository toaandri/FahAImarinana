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


class LoginRequest(BaseModel):
    email: str
    mot_de_passe: str = Field(min_length=8)


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


class ChatSessionCreate(BaseModel):
    titre: str = Field(default="Investigation", min_length=1, max_length=250)


class ChatSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    utilisateur_id: int
    titre: str
    cree_le: datetime
    mise_a_jour_le: datetime


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: str
    contenu: str
    citations: list[dict[str, Any]]
    horodatage: datetime


class ResearchQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=2_000)
    session_id: int | None = None


class ResearchAnswer(BaseModel):
    reponse: str
    citations: list[dict[str, Any]]
    chronologie: list[dict[str, Any]]


class MaharavoResearchRequest(BaseModel):
    sujet: str = Field(min_length=3, max_length=500)
    questions: list[str] = Field(default_factory=list, max_length=10)
    periode: str | None = Field(default=None, max_length=100)
    langues: list[str] = Field(default_factory=lambda: ["fr"], max_length=5)
    territoire: str | None = Field(default=None, max_length=150)


class MaharavoResearchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    utilisateur_id: int
    sujet: str
    questions: list[str]
    periode: str | None
    langues: list[str]
    territoire: str | None
    requetes: list[str]
    documents_ouverts: list[dict[str, Any]]
    citations: list[dict[str, Any]]
    synthese: str | None
    erreurs: list[str]
    statut: str
    modele: str
    debut: datetime
    fin: datetime | None


class MediaAnalysisRequest(BaseModel):
    type_media: Literal["image", "video", "audio", "document"]
    reference_originale: str = Field(min_length=1, max_length=500)
    empreinte_sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    outil: str = Field(min_length=1, max_length=150)
    version_outil: str = Field(min_length=1, max_length=80)
    observations: list[str] = Field(default_factory=list, max_length=50)
    indice_indicatif: Literal["non_evalue", "faible", "moyen", "eleve"] = "non_evalue"
    limites: list[str] = Field(default_factory=list, max_length=20)


class MediaAnalysisRead(MediaAnalysisRequest):
    model_config = ConfigDict(from_attributes=True)

    id: int
    utilisateur_id: int
    cree_le: datetime


class ConfidenceRequest(BaseModel):
    objet_type: Literal["signal", "draft", "research", "media"]
    objet_id: int = Field(gt=0)
    identite_source: Literal["non_evalue", "faible", "moyen", "eleve"]
    solidite_preuves: Literal["non_evalue", "faible", "moyen", "eleve"]
    validation_editoriale: Literal["non_evalue", "faible", "moyen", "eleve"]
    conclusion: Literal[
        "confirme", "infirme", "trompeur_hors_contexte",
        "partiellement_confirme", "non_verifiable"
    ]
    justification: str = Field(min_length=1, max_length=5000)


class ConfidenceRead(ConfidenceRequest):
    model_config = ConfigDict(from_attributes=True)

    id: int
    utilisateur_id: int
    cree_le: datetime
