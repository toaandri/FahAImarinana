from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from ....database import get_public_db
from ....repositories.publications import PublicPublicationRepository
from ....schemas import ArticlePublicRead

router = APIRouter(prefix="/public", tags=["Frontend public"])


@router.get('/gdelt')
def gdelt_news(response: Response):
    from ....services.gdelt import latest_news
    response.headers['Cache-Control'] = 'public, max-age=300'
    return latest_news()


@router.get("/articles", response_model=list[ArticlePublicRead])
def list_certified_articles(db: Session = Depends(get_public_db),
                           limit: int=Query(default=50,ge=1,le=200),offset: int=Query(default=0,ge=0)):
    return PublicPublicationRepository(db).published(limit=limit,offset=offset)


@router.get('/sync')
def synchronize(request: Request,db: Session=Depends(get_public_db)):
    from ....services.synchronization import public_snapshot
    snapshot=public_snapshot(db)
    etag='"'+snapshot['snapshot_version']+'"'
    headers={'ETag':etag,'Cache-Control':'no-cache',
             'X-Synchronized-At':snapshot['synchronized_at']}
    if request.headers.get('if-none-match')==etag:
        return Response(status_code=304,headers=headers)
    return JSONResponse(snapshot,headers=headers)
