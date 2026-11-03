"""Transactional session lifecycle, single-use invitations and rotating refresh tokens."""
from datetime import timedelta
import hashlib
import hmac
import secrets
from uuid import uuid4
from jose import jwt, JWTError
from sqlalchemy import select
from ..core.config import get_settings
from ..core.errors import AuthenticationError,ConflictError,ForbiddenError,NotFoundError
from ..core.security import (create_access_token,password_hash,password_matches,now,utc,DUMMY_PASSWORD_HASH)
from ..database.scope import set_scope,scope_for_user
from ..models import User,AuthSession,RefreshToken,Invitation,Newsroom
from ..repositories.identity import UserRepository
from ..schemas.auth import TokenRead


def secret_hash(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def new_secret():
    return uuid4().hex+'.'+secrets.token_urlsafe(48)


def secret_id(value):
    parts=value.split('.')
    if len(parts)!=2 or len(parts[0])!=32 or len(parts[1])!=64:
        raise AuthenticationError('Identifiant secret invalide.')
    return parts[0]


def _pair(db,user,session):
    secret=new_secret()
    db.add(RefreshToken(id=secret_id(secret),session_id=session.id,token_hash=secret_hash(secret),expires_at=session.expires_at))
    settings=get_settings()
    return TokenRead(access_token=create_access_token(user,session_id=session.id),refresh_token=secret,
        expires_in=settings.jwt_expire_minutes*60,
        refresh_expires_in=max(0,int((utc(session.expires_at)-now()).total_seconds())),session_id=session.id)


def issue_tokens(db,user,*,user_agent=''):
    scope_for_user(db,user)
    session=AuthSession(user_id=user.id,auth_version=user.auth_version,
        expires_at=now()+timedelta(days=get_settings().refresh_expire_days),user_agent=user_agent[:250])
    db.add(session); db.flush()
    pair=_pair(db,user,session)
    db.commit()
    return pair


def register_user(db,payload,*,user_agent=''):
    settings=get_settings()
    set_scope(db,settings.default_newsroom_id,settings.default_dataset)
    if UserRepository(db).by_email(payload.email):
        raise ConflictError('Email déjà utilisé.')
    newsroom=db.scalar(select(Newsroom).where(
        Newsroom.id==settings.default_newsroom_id,
        Newsroom.dataset==settings.default_dataset,
        Newsroom.status=='active',
    ))
    if newsroom is None:
        raise ForbiddenError('La rédaction par défaut est indisponible.')
    user=User(email=payload.email,mot_de_passe_hash=password_hash(payload.mot_de_passe),role='LECTEUR')
    db.add(user); db.flush()
    return issue_tokens(db,user,user_agent=user_agent)


def login_user(db,payload,*,user_agent='',service=False):
    email=payload.client_id.strip().lower() if service else payload.email
    password=payload.client_secret if service else payload.mot_de_passe
    user=UserRepository(db).get_active_by_email(email)
    matched=password_matches(password,user.mot_de_passe_hash if user else DUMMY_PASSWORD_HASH)
    if (not matched or user is None or not user.actif or user.status!='active'
        or (user.account_type=='service')!=service):
        raise AuthenticationError('Identifiants invalides.')
    scope_for_user(db,user)
    if not user.mot_de_passe_hash.startswith('scrypt$'):
        user.mot_de_passe_hash=password_hash(password)
    return issue_tokens(db,user,user_agent=user_agent)


def refresh_tokens(db,secret):
    identifier=secret_id(secret)
    candidate=db.scalar(select(RefreshToken).where(RefreshToken.id==identifier)
                        .execution_options(authentication_lookup=True))
    if candidate is None or not hmac.compare_digest(candidate.token_hash,secret_hash(secret)):
        raise AuthenticationError('Refresh token invalide ou révoqué.')
    set_scope(db,candidate.newsroom_id,candidate.dataset)
    session=db.scalar(select(AuthSession).where(AuthSession.id==candidate.session_id).with_for_update()
                      .execution_options(populate_existing=True))
    token=db.scalar(select(RefreshToken).where(RefreshToken.id==identifier).with_for_update()
                    .execution_options(populate_existing=True))
    if token.used_at is not None:
        session.revoked_at=now(); session.revocation_reason='refresh_reuse'
        db.commit()  # Commit revocation even though the request is denied.
        raise AuthenticationError('Refresh token réutilisé ; session révoquée.')
    user=UserRepository(db).get_for_auth(session.user_id)
    if (session.revoked_at or utc(session.expires_at)<=now() or utc(token.expires_at)<=now()
        or user is None or not user.actif or user.status!='active' or user.auth_version!=session.auth_version
        or (user.newsroom_id,user.dataset)!=(session.newsroom_id,session.dataset)):
        raise AuthenticationError('Session expirée ou révoquée.')
    token.used_at=now()
    pair=_pair(db,user,session)
    db.commit()
    return pair


def revoke_session(db,user,identifier,*,reason='logout'):
    scope_for_user(db,user)
    session=db.scalar(select(AuthSession).where(AuthSession.id==identifier,AuthSession.user_id==user.id).with_for_update())
    if session is None:
        raise NotFoundError('Session introuvable.')
    session.revoked_at=now(); session.revocation_reason=reason
    db.commit()


def revoke_all(db,user,*,reason='logout_all'):
    scope_for_user(db,user)
    for session in db.scalars(select(AuthSession).where(AuthSession.user_id==user.id,AuthSession.revoked_at.is_(None)).with_for_update()):
        session.revoked_at=now(); session.revocation_reason=reason
    db.commit()


def change_password(db,user,payload):
    scope_for_user(db,user)
    if user.account_type!='human' or not password_matches(payload.current_password,user.mot_de_passe_hash):
        raise AuthenticationError('Mot de passe actuel invalide.')
    user.mot_de_passe_hash=password_hash(payload.new_password)
    user.auth_version+=1
    revoke_all(db,user,reason='password_changed')

def update_profile(db,user,payload):
    email = payload.email.strip().lower()
    existing = UserRepository(db).by_email(email)
    if existing is not None and existing.id != user.id:
        raise ConflictError('Email déjà utilisé.')
    user.name = payload.name.strip()
    user.email = email
    db.commit()
    return user

def request_password_reset(db, payload):
    user = UserRepository(db).get_active_by_email(payload.email)
    if user is None:
        return {'message': 'Si ce compte existe, un lien de récupération sera envoyé.'}
    settings = get_settings()
    token = jwt.encode({'sub': str(user.id), 'type': 'password_reset',
                        'exp': now() + timedelta(minutes=15)},
                       settings.jwt_secret.get_secret_value(), algorithm='HS256')
    return {'message': 'Jeton de récupération généré pour le canal de notification configuré.',
            'reset_token': token}

def reset_password(db, payload):
    settings = get_settings()
    try:
        claims = jwt.decode(payload.reset_token, settings.jwt_secret.get_secret_value(),
                            algorithms=['HS256'])
        if claims.get('type') != 'password_reset':
            raise ValueError('type')
        user = UserRepository(db).get_for_auth(int(claims['sub']))
    except (JWTError, KeyError, TypeError, ValueError):
        raise AuthenticationError('Jeton de récupération invalide ou expiré.') from None
    if user is None or not user.actif or user.status != 'active':
        raise AuthenticationError('Compte inactif.')
    user.mot_de_passe_hash = password_hash(payload.new_password)
    user.auth_version += 1
    revoke_all(db, user, reason='password_reset')
    return {'message': 'Mot de passe réinitialisé.'}
