from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from ..database.base import Base


class DocumentRecherche(Base):
    __tablename__ = "documents_recherche"

    id: Mapped[int] = mapped_column(primary_key=True)
    titre: Mapped[str] = mapped_column(String(250))
    contenu: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(500))
    est_certifie: Mapped[bool] = mapped_column(Boolean, default=False)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SessionChat(Base):
    __tablename__ = "sessions_chat"

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    titre: Mapped[str] = mapped_column(String(250), default="Investigation")
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    mise_a_jour_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MessageChat(Base):
    __tablename__ = "messages_chat"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions_chat.id"))
    role: Mapped[str] = mapped_column(String(20))
    contenu: Mapped[str] = mapped_column(Text)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    horodatage: Mapped[datetime] = mapped_column(DateTime(timezone=True))
