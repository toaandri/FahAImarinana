"""Fail-closed ASGI guard, before parsing private request bodies."""
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from ..database import SessionLocal
from ..core.security import authenticate_token
from ..core.rbac import authorize
from ..core.errors import DomainError,AuthenticationError
from ..core.route_policies import PUBLIC_ROUTES,canonical_api_path,policy_for


class AuthorizationMiddleware:
    def __init__(self,app):
        self.app=app

    def check(self,token,permission):
        with SessionLocal() as db:
            user=authenticate_token(db,token)
            if permission is not None:
                authorize(user,permission)
            return {'user_id':user.id,'session_id':db.info['auth_session_id']}

    async def __call__(self,scope,receive,send):
        if scope['type']!='http' or scope['method']=='OPTIONS':
            return await self.app(scope,receive,send)
        path=canonical_api_path(scope['path']); method=scope['method']
        if path is None or (method,path) in PUBLIC_ROUTES:
            return await self.app(scope,receive,send)
        found,permission=policy_for(method,path)
        if not found:
            return await JSONResponse({'detail':'Route introuvable.'},status_code=404)(scope,receive,send)
        headers=dict(scope.get('headers',[])); authorization=headers.get(b'authorization',b'').decode('latin1')
        try:
            if not authorization.lower().startswith('bearer '):
                raise AuthenticationError('Authentification requise.')
            principal=await run_in_threadpool(self.check,authorization[7:],permission)
        except DomainError as exc:
            extra={'WWW-Authenticate':'Bearer'} if exc.status_code==401 else {}
            return await JSONResponse({'detail':str(exc)},status_code=exc.status_code,headers=extra)(scope,receive,send)
        except SQLAlchemyError:
            return await JSONResponse({'detail':'Authentification temporairement indisponible.'},status_code=503)(scope,receive,send)
        scope.setdefault('state',{})['principal']=principal
        await self.app(scope,receive,send)
