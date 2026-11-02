from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from sqlalchemy.types import JSON
from ..database.base import Base
from .common import ScopedRecord, scope_args, scoped_fk

class Source(ScopedRecord, Base):
    __tablename__ = 'sources'
    __table_args__ = (*scope_args('sources', public=False),
        CheckConstraint("type IN ('Facebook','X','Web','RSS')", name="ck_sources_type"),
        CheckConstraint("statut IN ('Actif','Inactif')", name="ck_sources_status"),
        CheckConstraint("frequence_scan_secondes >= 60", name="ck_sources_frequency"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(150))
    type: Mapped[str] = mapped_column(String(30))
    url: Mapped[str] = mapped_column(String(500))
    statut: Mapped[str] = mapped_column(String(15), default="Actif")
    frequence_scan_secondes: Mapped[int] = mapped_column(Integer, default=900)
    derniere_verification: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    name = synonym("nom")
    status = synonym("statut")
    signals: Mapped[list["Signal"]] = relationship(primaryjoin="Source.id == Signal.source_id", foreign_keys="Signal.source_id", back_populates="source", passive_deletes=True)


class Signal(ScopedRecord, Base):
    __tablename__ = 'signals'
    __table_args__ = (*scope_args('signals', public=False),
        scoped_fk("source_id", "sources", name="fk_signals_source_scope"),
        scoped_fk("case_id", "cases", name="fk_signals_case_scope"),
        CheckConstraint("status IN ('new','triaged','investigating','archived')", name="ck_signals_status"),
        CheckConstraint("nombre_interactions >= 0", name="ck_signals_interactions"),
        CheckConstraint("niveau_viralite >= 0 AND niveau_viralite <= 100", name="ck_signals_virality"),
        Index("ix_signals_source_date", "source_id", "horodatage_publication"),
        Index("ix_signals_urgent", "newsroom_id", "dataset", "est_urgent", "horodatage_publication"),
        Index("ix_signals_case", "case_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(Integer)
    contenu_brut: Mapped[str] = mapped_column(Text)
    contenu_normalise: Mapped[str] = mapped_column(Text)
    url_origine: Mapped[str] = mapped_column(String(500))
    horodatage_publication: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    auteur: Mapped[str | None] = mapped_column(String(150))
    nombre_interactions: Mapped[int] = mapped_column(Integer, default=0)
    niveau_viralite: Mapped[float] = mapped_column(Float, default=0)
    mots_cles_detectes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    est_urgent: Mapped[bool] = mapped_column(Boolean, default=False)

    case_id: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="new")
    raw_content = synonym("contenu_brut")
    source: Mapped["Source"] = relationship(primaryjoin="Signal.source_id == Source.id", foreign_keys=[source_id], back_populates="signals")
    case: Mapped["Case | None"] = relationship(primaryjoin="Signal.case_id == Case.id", foreign_keys=[case_id], back_populates="signals")
    draft: Mapped["Draft | None"] = relationship(primaryjoin="Signal.id == Draft.signal_id", foreign_keys="Draft.signal_id", back_populates="signal", passive_deletes=True)
