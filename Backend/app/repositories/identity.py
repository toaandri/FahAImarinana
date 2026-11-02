from sqlalchemy import select
from ..models import Utilisateur, ContactJournaliste
from .base import Repository


class UserRepository(Repository[Utilisateur]):
    model = Utilisateur

    def by_email(self, email: str):
        return self.db.scalar(select(Utilisateur).where(Utilisateur.email == email).execution_options(authentication_lookup=True))


    def get_for_auth(self, identifier):
        return self.db.scalar(select(Utilisateur).where(Utilisateur.id == identifier)
                              .execution_options(authentication_lookup=True))


class ContactRepository(Repository[ContactJournaliste]):
    model = ContactJournaliste

    def active(self):
        return list(self.db.scalars(select(ContactJournaliste).join(Utilisateur).where(
            ContactJournaliste.alertes_actives.is_(True), Utilisateur.actif.is_(True), Utilisateur.status == "active")))
