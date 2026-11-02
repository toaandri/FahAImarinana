from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ....database import get_db
from ....models import ArticleCertifie
from ....schemas import ArticlePublicRead

router = APIRouter(prefix="/public", tags=["Frontend public"])


@router.get("/articles", response_model=list[ArticlePublicRead])
def list_certified_articles(db: Session = Depends(get_db)):
    """Public frontend feed: it can only read human-certified articles."""
    return list(
        db.scalars(
            select(ArticleCertifie)
            .where(ArticleCertifie.statut_verification.in_(("Vrai", "Faux", "Trompeur")))
            .order_by(ArticleCertifie.horodatage_validation.desc())
        )
    )
