
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database.base import Base


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="Journaliste")
    actif: Mapped[bool] = mapped_column(Boolean, default=True)


class ContactJournaliste(Base):
    __tablename__ = "contacts_journalistes"

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    numero_telephone: Mapped[str] = mapped_column(String(30), unique=True)
    alertes_actives: Mapped[bool] = mapped_column(Boolean, default=True)
