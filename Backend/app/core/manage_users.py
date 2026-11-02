"""Operator CLI for provisioning an approved editorial account."""
import argparse
from getpass import getpass
from ..database import SessionLocal
from ..models import Utilisateur
from ..repositories.identity import UserRepository
from ..schemas.auth import UserCreate
from .security import password_hash


def main() -> None:
    parser = argparse.ArgumentParser(description="Créer un compte approuvé par la rédaction.")
    parser.add_argument('--email', required=True)
    parser.add_argument('--role', choices=['Journaliste', 'Editeur'], default='Journaliste')
    args = parser.parse_args()
    password = getpass('Mot de passe : ')
    if password != getpass('Confirmer : '):
        parser.error('Les mots de passe diffèrent.')
    payload = UserCreate(email=args.email, mot_de_passe=password)
    with SessionLocal() as db:
        if UserRepository(db).by_email(payload.email):
            parser.error('Email déjà utilisé.')
        user = Utilisateur(email=payload.email, mot_de_passe_hash=password_hash(payload.mot_de_passe), role=args.role)
        UserRepository(db).add(user)
        db.commit()
    print('Compte créé ; connexion disponible via /api/auth/login.')


if __name__ == '__main__':
    main()
