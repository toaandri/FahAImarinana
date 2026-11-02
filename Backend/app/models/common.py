"""Shared lifecycle and isolation rules. No private entity can become public."""
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column


def utcnow():
    return datetime.now(timezone.utc)


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, server_default=func.now())


class ScopedRecord(Timestamps):
    newsroom_id: Mapped[int] = mapped_column(Integer, default=1)
    dataset: Mapped[str] = mapped_column(String(15), default="real")
    confidentiality: Mapped[str] = mapped_column(String(15), default="private")


def scope_args(table: str, *, public: bool = False):
    visibility = "'private','confidential','public'" if public else "'private','confidential'"
    return (
        UniqueConstraint("id", "newsroom_id", "dataset", name=f"uq_{table}_scope"),
        ForeignKeyConstraint(["newsroom_id", "dataset"], ["newsrooms.id", "newsrooms.dataset"],
                             name=f"fk_{table}_newsroom", ondelete="RESTRICT"),
        CheckConstraint("dataset IN ('real','demo','quarantine')", name=f"ck_{table}_dataset"),
        CheckConstraint(f"confidentiality IN ({visibility})", name=f"ck_{table}_confidentiality"),
        Index(f"ix_{table}_scope_created", "newsroom_id", "dataset", "created_at"),
    )


def scoped_fk(column: str, parent: str, *, name: str):
    return ForeignKeyConstraint(
        [column, "newsroom_id", "dataset"], [f"{parent}.id", f"{parent}.newsroom_id", f"{parent}.dataset"],
        name=name, ondelete="RESTRICT",
    )


def case_link(column: str, parent: str, *, name: str):
    return ForeignKeyConstraint(
        [column, "case_id", "newsroom_id", "dataset"],
        [f"{parent}.id", f"{parent}.case_id", f"{parent}.newsroom_id", f"{parent}.dataset"],
        name=name, ondelete="RESTRICT",
    )
