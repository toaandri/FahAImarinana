from sqlalchemy import select
from ..models import DocumentRecherche, SessionChat, MessageChat
from .base import Repository


class ResearchRepository(Repository[DocumentRecherche]):
    model = DocumentRecherche

    def by_article(self, article_id: int):
        return self.db.scalar(select(DocumentRecherche).where(DocumentRecherche.url == f"article:{article_id}"))

    def certified(self):
        return list(self.db.scalars(select(DocumentRecherche).where(DocumentRecherche.est_certifie.is_(True))))


class ChatRepository(Repository[SessionChat]):
    model = SessionChat

    def for_user(self, user_id: int):
        return list(self.db.scalars(select(SessionChat).where(SessionChat.utilisateur_id == user_id)
                                    .order_by(SessionChat.mise_a_jour_le.desc())))

    def messages(self, session_id: int):
        return list(self.db.scalars(select(MessageChat).where(MessageChat.session_id == session_id)
                                    .order_by(MessageChat.horodatage.asc(), MessageChat.id.asc())))
