from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ....database import get_public_db
from ....repositories.publications import PublicPublicationRepository
from ....schemas import ArticlePublicRead

router = APIRouter(prefix="/public", tags=["Frontend public"])


@router.get("/articles", response_model=list[ArticlePublicRead])
def list_certified_articles(db: Session = Depends(get_public_db)):
    return PublicPublicationRepository(db).published()
