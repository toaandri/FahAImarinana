from datetime import datetime
from typing import Any
from sqlalchemy import CheckConstraint, DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from sqlalchemy.types import JSON
from ..database.base import Base
from .common import ScopedRecord, scope_args, scoped_fk, case_link

class Draft(ScopedRecord, Base):
    __tablename__ = 'drafts'
    __table_args__ = (*scope_args('drafts', public=False),
        UniqueConstraint("signal_id", name="uq_drafts_ia_signal_id"),
        scoped_fk("signal_id", "signals", name="fk_drafts_signal_scope"),
        scoped_fk("case_id", "cases", name="fk_drafts_case_scope"),
        case_link("claim_id", "claims", name="fk_drafts_claim_case"),
        CheckConstraint("claim_id IS NULL OR case_id IS NOT NULL", name="ck_drafts_claim_case"),
        CheckConstraint("statut IN ('En_Attente','En_Cours','Rejete')", name="ck_drafts_status"),
        CheckConstraint("score_credibilite_indicatif >= 0 AND score_credibilite_indicatif <= 100", name="ck_drafts_score"),
        Index("ix_drafts_status", "newsroom_id", "dataset", "statut", "horodatage"),
        Index("ix_drafts_case", "case_id"),
        Index("ix_drafts_claim", "claim_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    signal_id: Mapped[int] = mapped_column(Integer)
    titre_suggere: Mapped[str] = mapped_column(String(250))
    synthese_ia: Mapped[str] = mapped_column(Text)
    score_credibilite_indicatif: Mapped[float] = mapped_column(Float)
    sources_croisees: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    statut: Mapped[str] = mapped_column(String(25), default="En_Attente")
    horodatage: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    case_id: Mapped[int | None] = mapped_column(Integer)
    claim_id: Mapped[int | None] = mapped_column(Integer)
    title = synonym("titre_suggere")
    status = synonym("statut")
    signal: Mapped["Signal"] = relationship(primaryjoin="Draft.signal_id == Signal.id", foreign_keys=[signal_id], back_populates="draft")
    case: Mapped["Case | None"] = relationship(primaryjoin="Draft.case_id == Case.id", foreign_keys=[case_id], back_populates="drafts")
    claim: Mapped["Claim | None"] = relationship(primaryjoin="Draft.claim_id == Claim.id", foreign_keys=[claim_id], back_populates="drafts")
    publication: Mapped["Publication | None"] = relationship(primaryjoin="Draft.id == Publication.draft_id", foreign_keys="Publication.draft_id", back_populates="draft", passive_deletes=True)


class Publication(ScopedRecord, Base):
    __tablename__ = 'publications'
    __table_args__ = (*scope_args('publications', public=True),
        UniqueConstraint("draft_id", name="uq_publications_draft"),
        scoped_fk("draft_id", "drafts", name="fk_publications_draft_scope"),
        scoped_fk("id_journaliste_validateur", "users", name="fk_publications_validator_scope"),
        CheckConstraint("status IN ('scheduled','published','withdrawn','archived')", name="ck_publications_status"),
        CheckConstraint("statut_verification IN ('Vrai','Faux','Trompeur')", name="ck_publications_verdict"),
        CheckConstraint("revision >= 1", name="ck_publications_revision"),
        CheckConstraint("confidentiality != 'public' OR (status = 'published' AND published_at IS NOT NULL)", name="ck_publications_release"),
        Index("ix_publications_public", "newsroom_id", "dataset", "confidentiality", "status", "published_at"),
        Index("ix_publications_validator", "id_journaliste_validateur"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int | None] = mapped_column(Integer)
    titre_final: Mapped[str] = mapped_column(String(250))
    corps_article: Mapped[str] = mapped_column(Text)
    categorie: Mapped[str] = mapped_column(String(50))
    statut_verification: Mapped[str] = mapped_column(String(20))
    id_journaliste_validateur: Mapped[int] = mapped_column(Integer)
    horodatage_validation: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    contenu_optimise_sms: Mapped[str] = mapped_column(String(480))

    status: Mapped[str] = mapped_column(String(20), default="published")
    revision: Mapped[int] = mapped_column(Integer, default=1)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    title = synonym("titre_final")
    body = synonym("corps_article")
    draft: Mapped["Draft | None"] = relationship(primaryjoin="Publication.draft_id == Draft.id", foreign_keys=[draft_id], back_populates="publication")
    validator: Mapped["User"] = relationship(primaryjoin="Publication.id_journaliste_validateur == User.id", foreign_keys=[id_journaliste_validateur])
    corrections: Mapped[list["CorrectionAudit"]] = relationship(primaryjoin="Publication.id == CorrectionAudit.publication_id", foreign_keys="CorrectionAudit.publication_id", back_populates="publication", passive_deletes=True)
    sms_exchanges: Mapped[list["SmsExchange"]] = relationship(primaryjoin="Publication.id == SmsExchange.publication_id", foreign_keys="SmsExchange.publication_id", back_populates="publication", passive_deletes=True)
