from sqlalchemy import CheckConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.base import Base
from .common import Timestamps


class Newsroom(Timestamps, Base):
    __tablename__ = "newsrooms"
    __table_args__ = (
        UniqueConstraint("id", "dataset", name="uq_newsrooms_dataset"),
        CheckConstraint("dataset IN ('real','demo','quarantine')", name="ck_newsrooms_dataset"),
        CheckConstraint("status IN ('active','archived')", name="ck_newsrooms_status"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    dataset: Mapped[str] = mapped_column(String(15), default="real")
    status: Mapped[str] = mapped_column(String(20), default="active")
    users: Mapped[list["User"]] = relationship(back_populates="newsroom", passive_deletes=True)
