from datetime import datetime
from typing import Any
from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from sqlalchemy.types import JSON
from ..database.base import Base
from .common import ScopedRecord, scope_args, scoped_fk, case_link

class ResearchJob(ScopedRecord, Base):
    __tablename__ = 'research_jobs'
    __table_args__ = (*scope_args('research_jobs', public=False),
        scoped_fk("utilisateur_id", "users", name="fk_research_user_scope"),
        scoped_fk("case_id", "cases", name="fk_research_case_scope"),
        case_link("claim_id", "claims", name="fk_research_claim_case"),
        CheckConstraint("claim_id IS NULL OR case_id IS NOT NULL", name="ck_research_claim_case"),
        CheckConstraint("statut IN ('queued','en_cours','terminee','partielle','echouee','cancelled')", name="ck_research_status"),
        CheckConstraint("fin IS NULL OR fin >= debut", name="ck_research_dates"),
        Index("ix_research_case", "case_id"),
        Index("ix_research_claim", "claim_id"),
        Index("ix_research_user", "utilisateur_id"),
        Index("ix_research_status", "newsroom_id", "dataset", "statut"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(Integer)
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

    case_id: Mapped[int | None] = mapped_column(Integer)
    claim_id: Mapped[int | None] = mapped_column(Integer)
    status = synonym("statut")
    user: Mapped["User"] = relationship(primaryjoin="ResearchJob.utilisateur_id == User.id", foreign_keys=[utilisateur_id])
    case: Mapped["Case | None"] = relationship(primaryjoin="ResearchJob.case_id == Case.id", foreign_keys=[case_id], back_populates="research_jobs")
    claim: Mapped["Claim | None"] = relationship(primaryjoin="ResearchJob.claim_id == Claim.id", foreign_keys=[claim_id])


class MediaAnalysis(ScopedRecord, Base):
    __tablename__ = 'media_analyses'
    __table_args__ = (*scope_args('media_analyses', public=False),
        scoped_fk("utilisateur_id", "users", name="fk_media_user_scope"),
        scoped_fk("case_id", "cases", name="fk_media_case_scope"),
        case_link("evidence_id", "evidence", name="fk_media_evidence_case"),
        CheckConstraint("evidence_id IS NULL OR case_id IS NOT NULL", name="ck_media_evidence_case"),
        CheckConstraint("status IN ('pending','running','completed','failed','reviewed')", name="ck_media_status"),
        CheckConstraint("type_media IN ('image','video','audio','document')", name="ck_media_type"),
        CheckConstraint("length(empreinte_sha256) = 64", name="ck_media_hash"),
        Index("ix_media_case", "case_id"),
        Index("ix_media_evidence", "evidence_id"),
        Index("ix_media_user", "utilisateur_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(Integer)
    type_media: Mapped[str] = mapped_column(String(20))
    reference_originale: Mapped[str] = mapped_column(String(500))
    empreinte_sha256: Mapped[str] = mapped_column(String(64))
    outil: Mapped[str] = mapped_column(String(150))
    version_outil: Mapped[str] = mapped_column(String(80))
    observations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    indice_indicatif: Mapped[str] = mapped_column(String(20))
    limites: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    case_id: Mapped[int | None] = mapped_column(Integer)
    evidence_id: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    user: Mapped["User"] = relationship(primaryjoin="MediaAnalysis.utilisateur_id == User.id", foreign_keys=[utilisateur_id])
    case: Mapped["Case | None"] = relationship(primaryjoin="MediaAnalysis.case_id == Case.id", foreign_keys=[case_id])
    evidence: Mapped["Evidence | None"] = relationship(primaryjoin="MediaAnalysis.evidence_id == Evidence.id", foreign_keys=[evidence_id], back_populates="media_analyses")


class EvaluationConfianceMaharavo(ScopedRecord, Base):
    __tablename__ = 'evaluations_confiance_maharavo'
    __table_args__ = (*scope_args('evaluations_confiance_maharavo', public=False),
        scoped_fk("utilisateur_id", "users", name="fk_confidence_user_scope"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(Integer)
    objet_type: Mapped[str] = mapped_column(String(30))
    objet_id: Mapped[int] = mapped_column(Integer)
    identite_source: Mapped[str] = mapped_column(String(20))
    solidite_preuves: Mapped[str] = mapped_column(String(20))
    validation_editoriale: Mapped[str] = mapped_column(String(20))
    conclusion: Mapped[str] = mapped_column(String(40))
    justification: Mapped[str] = mapped_column(Text)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))
