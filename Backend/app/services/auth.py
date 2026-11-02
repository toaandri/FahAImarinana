"""Transactional session lifecycle, single-use invitations and rotating refresh tokens."""
from datetime import timedelta
import hashlib
import hmac
import secrets
from uuid import uuid4
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
    if not payload.invitation_token:
        raise ForbiddenError('Une invitation nominative est requise.')
    identifier=secret_id(payload.invitation_token)
    invitation=db.scalar(select(Invitation).where(Invitation.id==identifier).with_for_update()
                         .execution_options(authentication_lookup=True))
    if (invitation is None or not hmac.compare_digest(invitation.token_hash,secret_hash(payload.invitation_token))
        or invitation.consumed_at is not None or utc(invitation.expires_at)<=now() or invitation.email!=payload.email):
        raise ForbiddenError('Invitation invalide, expirée ou déjà utilisée.')
    set_scope(db,invitation.newsroom_id,invitation.dataset)
    if UserRepository(db).by_email(payload.email):
        raise ConflictError('Email déjà utilisé.')
    newsroom=db.scalar(select(Newsroom).where(Newsroom.id==invitation.newsroom_id))
    inviter=UserRepository(db).get_for_auth(invitation.invited_by_id)
    if newsroom.status!='active' or inviter is None or not inviter.actif or inviter.status!='active' or inviter.role!='ADMINISTRATEUR':
        raise ForbiddenError('Cette invitation ne peut plus être utilisée.')
    user=User(email=payload.email,mot_de_passe_hash=password_hash(payload.mot_de_passe),role=invitation.role)
    invitation.consumed_at=now()
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
