"""Versioned scrypt hashes, legacy bcrypt verification and session-bound access JWTs."""
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from uuid import uuid4
import bcrypt
from jose import JWTError,jwt
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import get_settings
from .errors import AuthenticationError
from ..models import User,AuthSession,Newsroom
from ..repositories.identity import UserRepository

JWT_ALGORITHM='HS256'


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def now():
    return datetime.now(timezone.utc)


def password_hash(password: str) -> str:
    data=password.encode('utf-8')
    if not 8 <= len(password) <= 1024 or len(data)>4096:
        raise ValueError('Longueur de mot de passe invalide.')
    salt=secrets.token_bytes(16)
    digest=hashlib.scrypt(data,salt=salt,n=32768,r=8,p=1,maxmem=128*1024*1024,dklen=32)
    enc=lambda value:base64.urlsafe_b64encode(value).decode('ascii')
    return 'scrypt$32768$8$1$'+enc(salt)+'$'+enc(digest)


def password_matches(password: str,hashed: str) -> bool:
    if len(password)>1024 or len(password.encode('utf-8'))>4096:
        return False
    try:
        if hashed.startswith(('$2a$','$2b$','$2y$')):
            return bcrypt.checkpw(password.encode('utf-8'),hashed.encode('ascii'))
        method,n,r,p,salt,expected=hashed.split('$')
        if (method,n,r,p)!=('scrypt','32768','8','1'):
            return False
        digest=hashlib.scrypt(password.encode('utf-8'),salt=base64.urlsafe_b64decode(salt),
            n=32768,r=8,p=1,maxmem=128*1024*1024,dklen=32)
        return hmac.compare_digest(digest,base64.urlsafe_b64decode(expected))
    except (ValueError,TypeError,UnicodeError):
        return False


DUMMY_PASSWORD_HASH=password_hash('invalid-authentication-password')


def create_access_token(user: User, *, session_id: str) -> str:
    settings=get_settings(); timestamp=now()
    return jwt.encode({'sub':str(user.id),'sid':session_id,'role':user.role,'ver':user.auth_version,
        'jti':uuid4().hex,'type':'access','iat':timestamp,'nbf':timestamp,
        'exp':timestamp+timedelta(minutes=settings.jwt_expire_minutes),
        'iss':settings.jwt_issuer,'aud':settings.jwt_audience},
        settings.jwt_secret.get_secret_value(),algorithm=JWT_ALGORITHM)


def authenticate_token(db: Session,token: str) -> User:
    settings=get_settings()
    try:
        payload=jwt.decode(token,settings.jwt_secret.get_secret_value(),algorithms=[JWT_ALGORITHM],
            issuer=settings.jwt_issuer,audience=settings.jwt_audience,
            options={'require_exp':True,'require_sub':True,'require_iat':True,'require_nbf':True,
                     'require_iss':True,'require_aud':True})
        if payload.get('type')!='access' or not isinstance(payload.get('sid'),str) or len(payload['sid'])!=32:
            raise ValueError('Invalid token type/session')
        if not isinstance(payload.get('ver'),int) or not payload.get('jti'):
            raise ValueError('Missing token version/id')
        user_id=int(payload['sub'])
    except (JWTError,KeyError,TypeError,ValueError) as exc:
        raise AuthenticationError('Jeton d’authentification invalide ou expiré.') from exc
    user=UserRepository(db).get_for_auth(user_id)
    session=db.scalar(select(AuthSession).where(AuthSession.id==payload['sid'])
                      .execution_options(authentication_lookup=True))
    if (user is None or not user.actif or user.status!='active' or session is None
        or session.user_id!=user.id or session.revoked_at is not None or utc(session.expires_at)<=now()
        or session.auth_version!=user.auth_version or payload['ver']!=user.auth_version
        or (session.newsroom_id,session.dataset)!=(user.newsroom_id,user.dataset)):
        raise AuthenticationError('Session révoquée, expirée ou compte inactif.')
    # Role/scopes from the database are authoritative, never claims supplied by a caller.
    db.info['auth_session_id']=session.id
    db.info['actor_id']=user.id
    return user
