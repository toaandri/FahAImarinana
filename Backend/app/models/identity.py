from sqlalchemy import Boolean, CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from ..database.base import Base
from .common import ScopedRecord, scope_args, scoped_fk

class User(ScopedRecord, Base):
    __tablename__ = 'users'
    __table_args__ = (*scope_args('users', public=False),
        CheckConstraint("role IN ('Journaliste','Editeur')", name="ck_users_role"),
        CheckConstraint("status IN ('active','suspended','archived')", name="ck_users_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="Journaliste")
    actif: Mapped[bool] = mapped_column(Boolean, default=True)

    status: Mapped[str] = mapped_column(String(20), default="active")
    password_hash = synonym("mot_de_passe_hash")
    newsroom: Mapped["Newsroom"] = relationship(back_populates="users")
    contacts: Mapped[list["ContactJournaliste"]] = relationship(primaryjoin="User.id == ContactJournaliste.utilisateur_id", foreign_keys="ContactJournaliste.utilisateur_id", back_populates="user", passive_deletes=True)


class ContactJournaliste(ScopedRecord, Base):
    __tablename__ = 'contacts_journalistes'
    __table_args__ = (*scope_args('contacts_journalistes', public=False),
        scoped_fk("utilisateur_id", "users", name="fk_contacts_user_scope"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(Integer)
    numero_telephone: Mapped[str] = mapped_column(String(30), unique=True)
    alertes_actives: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(primaryjoin="ContactJournaliste.utilisateur_id == User.id", foreign_keys=[utilisateur_id], back_populates="contacts")
