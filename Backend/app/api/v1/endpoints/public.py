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


@router.get('/news-image')
def news_image(url: str = Query(max_length=2000)):
    from urllib.parse import urlsplit
    import httpx
    from ....core.errors import NotFoundError, IntegrationUnavailableError
    from ....services.gdelt import latest_news
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or parsed.netloc != 'www.madagascar-tribune.com'
        or not parsed.path.startswith('/IMG/')
        or not any(item.get('image') == url for item in latest_news()['articles'])):
        raise NotFoundError('Image introuvable.')
    try:
        with httpx.stream('GET', url, timeout=8, follow_redirects=False,
                          headers={'User-Agent': 'FahAImarinana/1.0'}) as upstream:
            upstream.raise_for_status()
            content_type = upstream.headers.get('content-type', '').split(';')[0].lower()
            if content_type not in ('image/jpeg', 'image/png', 'image/webp', 'image/gif'):
                raise ValueError('Invalid image type')
            chunks, size = [], 0
            for chunk in upstream.iter_bytes():
                size += len(chunk)
                if size > 5 * 1024 * 1024:
                    raise ValueError('Image too large')
                chunks.append(chunk)
        return Response(content=b''.join(chunks), media_type=content_type,
                        headers={'Cache-Control': 'public, max-age=3600'})
    except (httpx.HTTPError, ValueError):
        raise IntegrationUnavailableError('Image momentanément indisponible.') from None


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
