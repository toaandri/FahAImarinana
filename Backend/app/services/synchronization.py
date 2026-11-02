"""Complete public snapshots: atomically replace the cache, including removals."""
import hashlib
import json
from datetime import datetime, timezone
from fastapi.encoders import jsonable_encoder
from ..schemas import ArticlePublicRead
from ..repositories.publications import PublicPublicationRepository
from ..core.errors import IntegrationUnavailableError


def public_snapshot(db):
    # A single SELECT provides a consistent statement snapshot on PostgreSQL.
    rows=PublicPublicationRepository(db).published(limit=2001)
    if len(rows)>2000:
        raise IntegrationUnavailableError('Flux trop volumineux pour une synchronisation complète ; cache conservé.')
    items=[]
    for row in rows:
        article=jsonable_encoder(ArticlePublicRead.model_validate(dict(row)).model_dump())
        version=hashlib.sha256(json.dumps(article,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        items.append({**article,'content_version':version})
    version=hashlib.sha256(json.dumps(items,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    return {'snapshot_version':version,'synchronized_at':datetime.now(timezone.utc).isoformat(),
            'complete':True,'strategy':'replace','items':items}
