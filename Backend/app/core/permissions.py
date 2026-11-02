from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from sqlalchemy.orm import Session
from ..database import get_db
from ..database.scope import scope_for_user
from ..models import User
from .security import authenticate_token
from .errors import AuthenticationError
from .rbac import Permission,authorize

bearer=HTTPBearer(auto_error=False)


def current_user(credentials: HTTPAuthorizationCredentials|None=Depends(bearer),db: Session=Depends(get_db))->User:
    if credentials is None:
        raise AuthenticationError('Authentification requise.')
    user=authenticate_token(db,credentials.credentials)
    scope_for_user(db,user)
    return user


class PermissionRequired:
    def __init__(self,permission):
        self.permission=Permission(permission)

    def __call__(self,user: User=Depends(current_user))->User:
        return authorize(user,self.permission)


def require_permission(permission):
    return PermissionRequired(permission)


# Import compatibility only; endpoints use named permissions explicitly.
journalist_or_editor=require_permission(Permission.CASE_READ)
