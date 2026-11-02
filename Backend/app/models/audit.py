from typing import Any
from sqlalchemy import CheckConstraint, Index, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.base import Base
from .common import ScopedRecord, scope_args, scoped_fk


class CorrectionAudit(ScopedRecord, Base):
    __tablename__ = "corrections_audit"
    __table_args__ = (*scope_args("corrections_audit"),
        scoped_fk("publication_id", "publications", name="fk_audit_publication_scope"),
        scoped_fk("actor_id", "users", name="fk_audit_actor_scope"),
        CheckConstraint("action IN ('published','corrected','withdrawn','restored')", name="ck_audit_action"),
        CheckConstraint("status = 'recorded'", name="ck_audit_status"),
        Index("ix_audit_publication_date", "publication_id", "created_at"),
        Index("ix_audit_actor", "actor_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    publication_id: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="recorded")
    reason: Mapped[str] = mapped_column(Text)
    before: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    after: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    publication: Mapped["Publication"] = relationship(primaryjoin="CorrectionAudit.publication_id == Publication.id", foreign_keys=[publication_id], back_populates="corrections")
    actor: Mapped["User"] = relationship(primaryjoin="CorrectionAudit.actor_id == User.id", foreign_keys=[actor_id])
