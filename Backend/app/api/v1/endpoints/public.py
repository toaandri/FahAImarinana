from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from html import escape
from urllib.parse import urlsplit
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


@router.get('/article', response_class=HTMLResponse, include_in_schema=False)
def public_article(id: int = Query(gt=0), db: Session = Depends(get_public_db)):
    article = PublicPublicationRepository(db).by_id(id)
    if article is None:
        raise HTTPException(status_code=404, detail='Article introuvable.')
    title = escape(article['titre_final'])
    body = escape(article['corps_article'])
    category = escape(article['categorie'])
    verdict = escape(article['statut_verification'])
    return HTMLResponse(f'''<!doctype html><html lang="fr"><head><meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{title} — FahAImarinana</title></head><body>
        <main><article><h1>{title}</h1><p>{category} · Statut : {verdict}</p>
        <div style="white-space:pre-wrap">{body}</div></article></main></body></html>''',
        headers={'Cache-Control': 'public, max-age=300'})


@router.get('/sitemap.xml', include_in_schema=False)
def public_sitemap(db: Session = Depends(get_public_db)):
    from ....core.config import get_settings
    base = get_settings().public_site_url.rstrip('/')
    parsed = urlsplit(base)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise HTTPException(status_code=503, detail='Configurer PUBLIC_SITE_URL avec l’adresse HTTPS publique du site.')
    articles = PublicPublicationRepository(db).published(limit=50000)
    entries = ''.join(f'<url><loc>{escape(base + "/api/v1/public/article?id=" + str(article["id"]))}</loc></url>' for article in articles)
    return Response('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                    + entries + '</urlset>', media_type='application/xml', headers={'Cache-Control': 'public, max-age=300'})


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
