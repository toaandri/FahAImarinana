from sqlalchemy import select, or_
from ..models import ArticleCertifie, DraftIA
from .base import Repository

VERIFIED_STATUSES = ("Vrai", "Faux", "Trompeur")


class DraftRepository(Repository[DraftIA]):
    model = DraftIA

    def by_signal(self, signal_id: int):
        return self.db.scalar(select(DraftIA).where(DraftIA.signal_id == signal_id))

    def lock(self, draft_id: int):
        return self.db.scalar(select(DraftIA).where(DraftIA.id == draft_id)
                              .with_for_update().execution_options(populate_existing=True))


class ArticleRepository(Repository[ArticleCertifie]):
    model = ArticleCertifie

    def published(self):
        return list(self.db.scalars(select(ArticleCertifie).where(
            ArticleCertifie.statut_verification.in_(VERIFIED_STATUSES)
        ).order_by(ArticleCertifie.horodatage_validation.desc(), ArticleCertifie.id.desc())))

    def matching(self, terms: list[str], limit: int):
        if not terms:
            return []
        filters = [ArticleCertifie.corps_article.contains(term, autoescape=True) for term in terms]
        # Lower both sides for case-insensitive matching, including SQLite tests.
        from sqlalchemy import func
        filters = [func.lower(ArticleCertifie.corps_article).contains(term.lower(), autoescape=True) for term in terms]
        return list(self.db.scalars(select(ArticleCertifie).where(
            ArticleCertifie.statut_verification.in_(VERIFIED_STATUSES), or_(*filters)
        ).order_by(ArticleCertifie.horodatage_validation.desc(), ArticleCertifie.id.desc()).limit(limit)))

    def by_draft(self, draft_id: int):
        return self.db.scalar(select(ArticleCertifie).where(ArticleCertifie.draft_id == draft_id).limit(1))
