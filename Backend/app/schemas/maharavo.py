from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


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
