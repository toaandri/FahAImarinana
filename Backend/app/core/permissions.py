from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Utilisateur
from .security import authenticate_token
from ..database.scope import scope_for_user
from .errors import AuthenticationError, ForbiddenError

bearer = HTTPBearer(auto_error=False)


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
                 db: Session = Depends(get_db)) -> Utilisateur:
    if credentials is None:
        raise AuthenticationError("Authentification requise.")
    user = authenticate_token(db, credentials.credentials)
    scope_for_user(db, user)
    return user


def journalist_or_editor(user: Utilisateur = Depends(current_user)) -> Utilisateur:
    if user.role not in {"Journaliste", "Editeur"}:
        raise ForbiddenError("Droits insuffisants.")
    return user
