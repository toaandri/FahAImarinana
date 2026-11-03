import secrets
from datetime import timedelta
from sqlalchemy import select
from ..core.rbac import Permission as P,authorize,Role
from ..core.errors import ForbiddenError,NotFoundError,ConflictError,ValidationDomainError
from ..core.security import password_hash,now
from ..core.config import get_settings
from ..database.scope import scope_for_user
from ..models import User,Invitation,AuthSession,TechnicalSetting
from ..repositories.identity import UserRepository
from .auth import new_secret,secret_id,secret_hash


def create_invitation(db,actor,payload):
    authorize(actor,P.USERS_MANAGE); scope_for_user(db,actor)
    if UserRepository(db).by_email(payload.email):
        raise ConflictError('Email déjà utilisé.')
    token=new_secret()
    invitation=Invitation(id=secret_id(token),email=payload.email,role=Role.JOURNALISTE.value,
        invited_by_id=actor.id,token_hash=secret_hash(token),
        expires_at=now()+timedelta(hours=get_settings().invitation_expire_hours))
    db.add(invitation); db.commit()
    return {'invitation_token':token,'email':invitation.email,'role':invitation.role,'expires_at':invitation.expires_at}


def create_service_account(db,actor,payload):
    authorize(actor,P.USERS_MANAGE); scope_for_user(db,actor)
    if UserRepository(db).by_email(payload.email):
        raise ConflictError('Email déjà utilisé.')
    secret=secrets.token_urlsafe(48)
    user=User(email=payload.email,role=Role.SERVICE_IA.value,account_type='service',
              mot_de_passe_hash=password_hash(secret),service_permissions=[p.value for p in payload.permissions])
    db.add(user); db.commit()
    return {'id':user.id,'client_id':user.email,'client_secret':secret,'permissions':user.service_permissions}


def update_account(db,actor,identifier,payload):
    authorize(actor,P.USERS_MANAGE); scope_for_user(db,actor)
    user=db.scalar(select(User).where(User.id==identifier).with_for_update())
    if user is None:
        raise NotFoundError('Compte introuvable.')
    if actor.id==user.id:
        raise ForbiddenError('Un compte ne peut pas modifier son propre statut.')
    user.status=payload.status; user.actif=payload.status=='active'
    user.auth_version+=1
    for session in db.scalars(select(AuthSession).where(AuthSession.user_id==user.id,AuthSession.revoked_at.is_(None))):
        session.revoked_at=now(); session.revocation_reason='account_changed'
    db.commit()
    return user


BOUNDS={'ingestion_batch_size':(1,100),'research_result_limit':(1,20)}


def set_technical_setting(db,actor,key,value):
    authorize(actor,P.SETTINGS_MANAGE); scope_for_user(db,actor)
    if key not in BOUNDS or not BOUNDS[key][0]<=value<=BOUNDS[key][1]:
        raise ValidationDomainError('Paramètre technique ou valeur non autorisés.')
    setting=db.scalar(select(TechnicalSetting).where(TechnicalSetting.key==key).with_for_update())
    if setting is None:
        setting=TechnicalSetting(key=key,value=value,updated_by_id=actor.id); db.add(setting)
    else:
        setting.value=value; setting.updated_by_id=actor.id
    db.commit()
    return {'key':setting.key,'value':setting.value}


def technical_setting(db,key,default):
    value=db.scalar(select(TechnicalSetting.value).where(TechnicalSetting.key==key))
    return default if value is None else value
