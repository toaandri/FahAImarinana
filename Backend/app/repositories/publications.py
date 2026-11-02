"""Read-only access to a whitelisted view, using the public DB dependency."""
from sqlalchemy import column, select, table, func
from ..core.config import get_settings
from ..database.public import FIELDS


class PublicPublicationRepository:
    def __init__(self, db):
        self.db = db
        settings = get_settings()
        self.newsroom_id = settings.public_newsroom_id
        name = 'demo_publications' if settings.public_dataset == 'demo' else 'public_publications'
        self.view = table(name, *(column(field) for field in FIELDS))

    def published(self, limit=None, offset=0):
        statement = select(self.view).where(self.view.c.newsroom_id == self.newsroom_id).order_by(
            self.view.c.horodatage_validation.desc(), self.view.c.id.desc())
        if limit is not None:
            statement=statement.limit(limit).offset(offset)
        return list(self.db.execute(statement).mappings())

    def matching(self, terms, limit=1):
        from sqlalchemy import or_
        if not terms:
            return []
        statement = select(self.view).where(
            self.view.c.newsroom_id == self.newsroom_id,
            or_(*(or_(func.lower(self.view.c.corps_article).contains(term.lower(), autoescape=True),
                      func.lower(self.view.c.titre_final).contains(term.lower(), autoescape=True)) for term in terms))
        ).order_by(self.view.c.horodatage_validation.desc(), self.view.c.id.desc()).limit(limit)
        return list(self.db.execute(statement).mappings())
