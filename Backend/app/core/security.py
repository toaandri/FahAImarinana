"""Password hashing and JWT verification, shared by HTTP and WebSocket."""
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from .config import get_settings
from .errors import AuthenticationError
from ..models import Utilisateur
from ..repositories.identity import UserRepository

JWT_ALGORITHM = "HS256"


def create_access_token(user: Utilisateur) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user.id), "role": user.role, "iat": now,
         "exp": now + timedelta(minutes=settings.jwt_expire_minutes)},
        settings.jwt_secret.get_secret_value(), algorithm=JWT_ALGORITHM,
    )


def authenticate_token(db: Session, token: str) -> Utilisateur:
    try:
        payload = jwt.decode(token, get_settings().jwt_secret.get_secret_value(),
                             algorithms=[JWT_ALGORITHM], options={"require_exp": True, "require_sub": True})
        user_id = int(payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError) as exc:
        raise AuthenticationError("Jeton d'authentification invalide.") from exc
    user = UserRepository(db).get_for_auth(user_id)
    if user is None or not user.actif or user.status != "active":
        raise AuthenticationError("Utilisateur inactif ou introuvable.")
    return user


def password_hash(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Le mot de passe ne doit pas dépasser 72 octets UTF-8.")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def password_matches(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False
