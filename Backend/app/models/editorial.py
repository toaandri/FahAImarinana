from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from ..database.base import Base


class DraftIA(Base):
    __tablename__ = "drafts_ia"
    __table_args__ = (UniqueConstraint("signal_id", name="uq_drafts_ia_signal_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey("signaux_bruts.id"))
    titre_suggere: Mapped[str] = mapped_column(String(250))
    synthese_ia: Mapped[str] = mapped_column(Text)
    score_credibilite_indicatif: Mapped[float] = mapped_column(Float)
    sources_croisees: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    statut: Mapped[str] = mapped_column(String(25), default="En_Attente")
    horodatage: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ArticleCertifie(Base):
    __tablename__ = "articles_certifies"

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int | None] = mapped_column(ForeignKey("drafts_ia.id"))
    titre_final: Mapped[str] = mapped_column(String(250))
    corps_article: Mapped[str] = mapped_column(Text)
    categorie: Mapped[str] = mapped_column(String(50))
    statut_verification: Mapped[str] = mapped_column(String(20))
    id_journaliste_validateur: Mapped[int] = mapped_column(Integer)
    horodatage_validation: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    contenu_optimise_sms: Mapped[str] = mapped_column(String(480))
