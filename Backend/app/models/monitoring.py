from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from ..database.base import Base


class SourceSurveillee(Base):
    __tablename__ = "sources_surveillees"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(150))
    type: Mapped[str] = mapped_column(String(30))
    url: Mapped[str] = mapped_column(String(500))
    statut: Mapped[str] = mapped_column(String(15), default="Actif")
    frequence_scan_secondes: Mapped[int] = mapped_column(Integer, default=900)
    derniere_verification: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SignalBrut(Base):
    __tablename__ = "signaux_bruts"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources_surveillees.id"))
    contenu_brut: Mapped[str] = mapped_column(Text)
    contenu_normalise: Mapped[str] = mapped_column(Text)
    url_origine: Mapped[str] = mapped_column(String(500))
    horodatage_publication: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    auteur: Mapped[str | None] = mapped_column(String(150))
    nombre_interactions: Mapped[int] = mapped_column(Integer, default=0)
    niveau_viralite: Mapped[float] = mapped_column(Float, default=0)
    mots_cles_detectes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    est_urgent: Mapped[bool] = mapped_column(Boolean, default=False)
