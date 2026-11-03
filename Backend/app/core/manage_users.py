"""Operator CLI for provisioning an approved editorial account."""
import argparse
from getpass import getpass
from ..database import SessionLocal
from ..database.scope import set_scope
from .config import get_settings
from ..models import Utilisateur
from ..repositories.identity import UserRepository
from ..schemas.auth import UserCreate
from .security import password_hash
from .rbac import Role


def main() -> None:
    parser = argparse.ArgumentParser(description="Créer un compte journaliste approuvé par la rédaction.")
    parser.add_argument('--email', required=True)
    args = parser.parse_args()
    password = getpass('Mot de passe : ')
    if password != getpass('Confirmer : '):
        parser.error('Les mots de passe diffèrent.')
    payload = UserCreate(email=args.email, mot_de_passe=password)
    with SessionLocal() as db:
        settings = get_settings()
        set_scope(db, settings.default_newsroom_id, settings.default_dataset)
        if UserRepository(db).by_email(payload.email):
            parser.error('Email déjà utilisé.')
        user = Utilisateur(email=payload.email, mot_de_passe_hash=password_hash(payload.mot_de_passe), role=Role.JOURNALISTE.value)
        UserRepository(db).add(user)
        db.commit()
    print('Compte créé ; connexion disponible via /api/auth/login.')


if __name__ == '__main__':
    main()
