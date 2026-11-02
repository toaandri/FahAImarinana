from sqlalchemy import select
from ..models import Utilisateur, ContactJournaliste, Newsroom
from .base import Repository


class UserRepository(Repository[Utilisateur]):
    model = Utilisateur

    def by_email(self, email: str):
        return self.db.scalar(select(Utilisateur).where(Utilisateur.email == email).execution_options(authentication_lookup=True))


    def get_for_auth(self, identifier):
        return self.db.scalar(select(Utilisateur).join(Newsroom).where(Utilisateur.id == identifier, Newsroom.status == "active")
                              .execution_options(authentication_lookup=True))


    def get_active_by_email(self,email):
        return self.db.scalar(select(Utilisateur).join(Newsroom).where(Utilisateur.email==email,Newsroom.status=='active')
                              .execution_options(authentication_lookup=True))


class ContactRepository(Repository[ContactJournaliste]):
    model = ContactJournaliste

    def active(self):
        return list(self.db.scalars(select(ContactJournaliste).join(Utilisateur).where(
            ContactJournaliste.alertes_actives.is_(True), Utilisateur.actif.is_(True), Utilisateur.status == "active")))
