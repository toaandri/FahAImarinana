from datetime import datetime
from typing import Any
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from ..database.base import Base
from .common import ScopedRecord, scope_args, scoped_fk

class DocumentRecherche(ScopedRecord, Base):
    __tablename__ = 'documents_recherche'
    __table_args__ = (*scope_args('documents_recherche', public=False),    )

    id: Mapped[int] = mapped_column(primary_key=True)
    titre: Mapped[str] = mapped_column(String(250))
    contenu: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(500))
    est_certifie: Mapped[bool] = mapped_column(Boolean, default=False)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SessionChat(ScopedRecord, Base):
    __tablename__ = 'sessions_chat'
    __table_args__ = (*scope_args('sessions_chat', public=False),
        scoped_fk("utilisateur_id", "users", name="fk_chat_user_scope"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(Integer)
    titre: Mapped[str] = mapped_column(String(250), default="Investigation")
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    mise_a_jour_le: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    messages: Mapped[list["MessageChat"]] = relationship(primaryjoin="SessionChat.id == MessageChat.session_id", foreign_keys="MessageChat.session_id", back_populates="session", passive_deletes=True)


class MessageChat(ScopedRecord, Base):
    __tablename__ = 'messages_chat'
    __table_args__ = (*scope_args('messages_chat', public=False),
        scoped_fk("session_id", "sessions_chat", name="fk_messages_session_scope"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(20))
    contenu: Mapped[str] = mapped_column(Text)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    horodatage: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    session: Mapped["SessionChat"] = relationship(primaryjoin="MessageChat.session_id == SessionChat.id", foreign_keys=[session_id], back_populates="messages")
