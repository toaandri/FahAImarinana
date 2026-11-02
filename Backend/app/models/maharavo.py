from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from ..database.base import Base


class RechercheMaharavo(Base):
    __tablename__ = "recherches_maharavo"

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    sujet: Mapped[str] = mapped_column(String(500))
    questions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    periode: Mapped[str | None] = mapped_column(String(100))
    langues: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    territoire: Mapped[str | None] = mapped_column(String(150))
    requetes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    documents_ouverts: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    synthese: Mapped[str | None] = mapped_column(Text)
    erreurs: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    statut: Mapped[str] = mapped_column(String(20), default="en_cours")
    modele: Mapped[str] = mapped_column(String(100))
    debut: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class AnalyseMediaMaharavo(Base):
    __tablename__ = "analyses_media_maharavo"

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    type_media: Mapped[str] = mapped_column(String(20))
    reference_originale: Mapped[str] = mapped_column(String(500))
    empreinte_sha256: Mapped[str] = mapped_column(String(64))
    outil: Mapped[str] = mapped_column(String(150))
    version_outil: Mapped[str] = mapped_column(String(80))
    observations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    indice_indicatif: Mapped[str] = mapped_column(String(20))
    limites: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class EvaluationConfianceMaharavo(Base):
    __tablename__ = "evaluations_confiance_maharavo"

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    objet_type: Mapped[str] = mapped_column(String(30))
    objet_id: Mapped[int] = mapped_column(Integer)
    identite_source: Mapped[str] = mapped_column(String(20))
    solidite_preuves: Mapped[str] = mapped_column(String(20))
    validation_editoriale: Mapped[str] = mapped_column(String(20))
    conclusion: Mapped[str] = mapped_column(String(40))
    justification: Mapped[str] = mapped_column(Text)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))
