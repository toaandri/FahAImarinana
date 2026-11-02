from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.base import Base
from .common import ScopedRecord, scope_args, scoped_fk, case_link


class Case(ScopedRecord, Base):
    __tablename__ = "cases"
    __table_args__ = (*scope_args("cases"),
        scoped_fk("created_by_id", "users", name="fk_cases_creator_scope"),
        CheckConstraint("status IN ('open','investigating','review','closed','archived')", name="ck_cases_status"),
        Index("ix_cases_status", "newsroom_id", "dataset", "status"),
        Index("ix_cases_creator", "created_by_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(250))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_by_id: Mapped[int] = mapped_column(Integer)
    creator: Mapped["User"] = relationship(primaryjoin="Case.created_by_id == User.id", foreign_keys=[created_by_id])
    claims: Mapped[list["Claim"]] = relationship(primaryjoin="Case.id == Claim.case_id", foreign_keys="Claim.case_id", back_populates="case", passive_deletes=True)
    evidence: Mapped[list["Evidence"]] = relationship(primaryjoin="Case.id == Evidence.case_id", foreign_keys="Evidence.case_id", back_populates="case", passive_deletes=True)
    signals: Mapped[list["Signal"]] = relationship(primaryjoin="Case.id == Signal.case_id", foreign_keys="Signal.case_id", back_populates="case", passive_deletes=True)
    drafts: Mapped[list["Draft"]] = relationship(primaryjoin="Case.id == Draft.case_id", foreign_keys="Draft.case_id", back_populates="case", passive_deletes=True)
    research_jobs: Mapped[list["ResearchJob"]] = relationship(primaryjoin="Case.id == ResearchJob.case_id", foreign_keys="ResearchJob.case_id", back_populates="case", passive_deletes=True)


class Claim(ScopedRecord, Base):
    __tablename__ = "claims"
    __table_args__ = (*scope_args("claims"),
        UniqueConstraint("id", "case_id", "newsroom_id", "dataset", name="uq_claims_case_scope"),
        scoped_fk("case_id", "cases", name="fk_claims_case_scope"),
        CheckConstraint("status IN ('unverified','investigating','verified','disputed','insufficient')", name="ck_claims_status"),
        CheckConstraint("verdict IN ('unknown','confirmed','refuted','misleading','partial','unverifiable')", name="ck_claims_verdict"),
        Index("ix_claims_case_status", "case_id", "status"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(Integer)
    statement: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="unverified")
    verdict: Mapped[str] = mapped_column(String(20), default="unknown")
    case: Mapped["Case"] = relationship(primaryjoin="Claim.case_id == Case.id", foreign_keys=[case_id], back_populates="claims")
    evidence_links: Mapped[list["ClaimEvidence"]] = relationship(primaryjoin="Claim.id == ClaimEvidence.claim_id", foreign_keys="ClaimEvidence.claim_id", back_populates="claim", passive_deletes=True)
    drafts: Mapped[list["Draft"]] = relationship(primaryjoin="Claim.id == Draft.claim_id", foreign_keys="Draft.claim_id", back_populates="claim", passive_deletes=True)


class Evidence(ScopedRecord, Base):
    __tablename__ = "evidence"
    __table_args__ = (*scope_args("evidence"),
        UniqueConstraint("id", "case_id", "newsroom_id", "dataset", name="uq_evidence_case_scope"),
        UniqueConstraint("newsroom_id", "dataset", "sha256", name="uq_evidence_hash_scope"),
        scoped_fk("case_id", "cases", name="fk_evidence_case_scope"),
        scoped_fk("source_id", "sources", name="fk_evidence_source_scope"),
        CheckConstraint("status IN ('collected','reviewing','verified','rejected')", name="ck_evidence_status"),
        CheckConstraint("kind IN ('document','image','video','audio','url','testimony')", name="ck_evidence_kind"),
        CheckConstraint("sha256 IS NULL OR length(sha256) = 64", name="ck_evidence_hash"),
        Index("ix_evidence_case_status", "case_id", "status"),
        Index("ix_evidence_source", "source_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(Integer)
    source_id: Mapped[int | None] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(250))
    kind: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    storage_key: Mapped[str | None] = mapped_column(String(500))
    original_url: Mapped[str | None] = mapped_column(String(500))
    sha256: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="collected")
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    case: Mapped["Case"] = relationship(primaryjoin="Evidence.case_id == Case.id", foreign_keys=[case_id], back_populates="evidence")
    source: Mapped["Source | None"] = relationship(primaryjoin="Evidence.source_id == Source.id", foreign_keys=[source_id])
    claim_links: Mapped[list["ClaimEvidence"]] = relationship(primaryjoin="Evidence.id == ClaimEvidence.evidence_id", foreign_keys="ClaimEvidence.evidence_id", back_populates="evidence", passive_deletes=True)
    media_analyses: Mapped[list["MediaAnalysis"]] = relationship(primaryjoin="Evidence.id == MediaAnalysis.evidence_id", foreign_keys="MediaAnalysis.evidence_id", back_populates="evidence", passive_deletes=True)


class ClaimEvidence(ScopedRecord, Base):
    __tablename__ = "claim_evidence"
    __table_args__ = (*scope_args("claim_evidence"),
        UniqueConstraint("claim_id", "evidence_id", name="uq_claim_evidence_pair"),
        case_link("claim_id", "claims", name="fk_claim_evidence_claim"),
        case_link("evidence_id", "evidence", name="fk_claim_evidence_evidence"),
        CheckConstraint("stance IN ('supports','refutes','context')", name="ck_claim_evidence_stance"),
        CheckConstraint("status IN ('proposed','reviewed','rejected')", name="ck_claim_evidence_status"),
        Index("ix_claim_evidence_reverse", "evidence_id", "claim_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(Integer)
    claim_id: Mapped[int] = mapped_column(Integer)
    evidence_id: Mapped[int] = mapped_column(Integer)
    stance: Mapped[str] = mapped_column(String(20), default="context")
    status: Mapped[str] = mapped_column(String(20), default="proposed")
    rationale: Mapped[str] = mapped_column(Text, default="")
    claim: Mapped["Claim"] = relationship(primaryjoin="ClaimEvidence.claim_id == Claim.id", foreign_keys=[claim_id], back_populates="evidence_links")
    evidence: Mapped["Evidence"] = relationship(primaryjoin="ClaimEvidence.evidence_id == Evidence.id", foreign_keys=[evidence_id], back_populates="claim_links")
