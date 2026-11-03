"""Bound media JSON before Pydantic allocates/decodes its base64 input."""
import asyncio
from starlette.responses import JSONResponse
from ..core.route_policies import canonical_api_path
from ..core.media import MAX_CONTRIBUTION_BODY_BYTES


class VideoBodyLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        route = (scope['method'], canonical_api_path(scope['path']))
        if route == ('POST', '/contributions/signals') or (
            route[0] == 'POST' and route[1] is not None
            and route[1].startswith('/contributions/') and route[1].endswith('/information')
        ):
            limit = MAX_CONTRIBUTION_BODY_BYTES
            too_large = 'Le média dépasse la taille maximale de 100 Mo.'
            timeout = 600
        elif route in (('POST', '/vision/video'), ('POST', '/vision/image')):
            limit = 6 * 1024 * 1024
            too_large = 'Le clip dépasse la taille autorisée.'
            timeout = 30
        elif route == ('PUT', '/auth/me/photo'):
            limit = 3 * 1024 * 1024
            too_large = 'La photo dépasse la taille autorisée.'
            timeout = 30
        else:
            return await self.app(scope, receive, send)
        chunks = []; size = 0
        try:
            async with asyncio.timeout(timeout):
                while True:
                    event = await receive()
                    if event['type'] == 'http.disconnect':
                        return
                    chunk = event.get('body', b''); size += len(chunk)
                    if size > limit:
                        return await JSONResponse({'detail': too_large},
                            status_code=413, headers={'Cache-Control': 'no-store'})(scope, receive, send)
                    chunks.append(chunk)
                    if not event.get('more_body', False):
                        break
        except TimeoutError:
            return await JSONResponse({'detail': 'Envoi du média trop lent ou interrompu.'},
                status_code=408, headers={'Cache-Control': 'no-store'})(scope, receive, send)
        body = b''.join(chunks)
        consumed = False

        async def bounded_receive():
            nonlocal consumed
            if not consumed:
                consumed = True
                return {'type': 'http.request', 'body': body, 'more_body': False}
            return await receive()
        await self.app(scope, bounded_receive, send)
