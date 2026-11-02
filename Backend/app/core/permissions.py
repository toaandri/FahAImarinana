from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Utilisateur
from .security import authenticate_token
from .errors import AuthenticationError, ForbiddenError

bearer = HTTPBearer(auto_error=False)


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
                 db: Session = Depends(get_db)) -> Utilisateur:
    if credentials is None:
        raise AuthenticationError("Authentification requise.")
    return authenticate_token(db, credentials.credentials)


def journalist_or_editor(user: Utilisateur = Depends(current_user)) -> Utilisateur:
    if user.role not in {"Journaliste", "Editeur"}:
        raise ForbiddenError("Droits insuffisants.")
    return user
