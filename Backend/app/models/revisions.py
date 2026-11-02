"""Private immutable snapshots; historical gaps are never reconstructed."""
from sqlalchemy import Integer, String, JSON, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from ..database.base import Base
from .common import ScopedRecord, scope_args, scoped_fk


class DraftRevision(ScopedRecord, Base):
    __tablename__ = 'draft_revisions'
    __table_args__ = (*scope_args('draft_revisions'),
        scoped_fk('draft_id', 'drafts', name='fk_revision_draft'),
        scoped_fk('actor_id', 'users', name='fk_revision_actor'),
        CheckConstraint('version >= 1', name='ck_revision_version'),
        CheckConstraint("event IN ('created','before_edit','edited','reviewed','validated','published')", name='ck_revision_event'),
        Index('ix_revision_draft', 'draft_id', 'id'),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer)
    event: Mapped[str] = mapped_column(String(20))
    snapshot: Mapped[dict] = mapped_column(JSON)
