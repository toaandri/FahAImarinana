from sqlalchemy.orm import Session
from ..core.config import get_settings
from ..core.errors import AuthenticationError, ConflictError, ForbiddenError
from ..core.security import create_access_token, password_hash, password_matches
from ..models import Utilisateur
from ..repositories.identity import UserRepository


def register_user(db: Session, payload) -> str:
    if not get_settings().allow_public_registration:
        raise ForbiddenError("Inscription publique désactivée. Contacter la rédaction.")
    email = payload.email.lower().strip()
    if UserRepository(db).by_email(email):
        raise ConflictError("Email déjà utilisé.")
    user = Utilisateur(email=email, mot_de_passe_hash=password_hash(payload.mot_de_passe), role="Journaliste")
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_access_token(user)


def login_user(db: Session, payload) -> str:
    user = UserRepository(db).by_email(payload.email.lower().strip())
    if user is None or not password_matches(payload.mot_de_passe, user.mot_de_passe_hash) or not user.actif:
        raise AuthenticationError("Identifiants invalides.")
    return create_access_token(user)
