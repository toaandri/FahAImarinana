from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Utilisateur
from .services import authenticate_token

bearer = HTTPBearer(auto_error=False)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Utilisateur:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentification requise.")
    try:
        return authenticate_token(db, credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def journalist_or_editor(user: Utilisateur = Depends(current_user)) -> Utilisateur:
    if user.role not in {"Journaliste", "Editeur"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Droits insuffisants.")
    return user
