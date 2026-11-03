"""Bounded per-process limiter. Reverse proxies must enforce shared production quotas."""
from collections import OrderedDict
import time
from starlette.responses import JSONResponse
from ..core.route_policies import canonical_api_path


class RateLimitMiddleware:
    def __init__(self,app,auth_limit=60,public_limit=60):
        self.app=app
        self.auth_limit=auth_limit
        self.public_limit=public_limit
        self.buckets=OrderedDict()

    async def __call__(self,scope,receive,send):
        if scope['type']!='http':
            return await self.app(scope,receive,send)
        path=canonical_api_path(scope['path']) or ''
        group='vision' if path=='/vision/video' else 'auth' if path in {'/auth/login','/auth/register','/auth/refresh','/auth/service-token'} else 'public'
        protected=(group in {'auth','vision'} and scope['method']=='POST') or path in {'/sms/citizen','/public/sync','/public/gdelt'}
        if protected:
            tick=time.monotonic()
            # ASGI event loop serializes this synchronous section; no await between read/write.
            address=(scope.get('client') or ('unknown',0))[0]
            key=(group,address)
            start,count=self.buckets.get(key,(tick,0))
            if tick-start>=60:
                start,count=tick,0
            limit=12 if group=='vision' else self.auth_limit if group=='auth' else self.public_limit
            if count>=limit:
                return await JSONResponse({'detail':'Trop de requêtes ; réessayez après le délai indiqué.'},
                    status_code=429,headers={'Retry-After':str(max(1,int(60-(tick-start))+1)),
                                            'Cache-Control':'no-store'})(scope,receive,send)
            self.buckets[key]=(start,count+1)
            self.buckets.move_to_end(key)
            if len(self.buckets)>10000:
                self.buckets.popitem(last=False)
        async def secure_send(message):
            if message['type']=='http.response.start':
                headers=list(message.get('headers',[]))
                names={key.lower() for key,_ in headers}
                if b'cache-control' not in names and not path.startswith('/public/'):
                    headers.append((b'cache-control',b'no-store'))
                headers.append((b'x-content-type-options',b'nosniff'))
                message={**message,'headers':headers}
            await send(message)
        await self.app(scope,receive,secure_send)
