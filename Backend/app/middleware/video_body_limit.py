"""Bound the video JSON before Pydantic allocates/decodes its base64 input."""
import asyncio
from starlette.responses import JSONResponse
from ..core.route_policies import canonical_api_path


class VideoBodyLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['method'] != 'POST' or canonical_api_path(scope['path']) != '/vision/video':
            return await self.app(scope, receive, send)
        limit = 6 * 1024 * 1024
        chunks = []; size = 0
        try:
            async with asyncio.timeout(30):
                while True:
                    event = await receive()
                    if event['type'] == 'http.disconnect':
                        return
                    chunk = event.get('body', b''); size += len(chunk)
                    if size > limit:
                        return await JSONResponse({'detail': 'Le clip dépasse la taille autorisée.'},
                            status_code=413, headers={'Cache-Control': 'no-store'})(scope, receive, send)
                    chunks.append(chunk)
                    if not event.get('more_body', False):
                        break
        except TimeoutError:
            return await JSONResponse({'detail': 'Envoi du clip trop lent ou interrompu.'},
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
