from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ....database import get_db
from ....models import Utilisateur
from ....schemas import LoginRequest, TokenRead, UserCreate
from ....services import create_access_token, password_hash, password_matches

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/register", response_model=TokenRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Utilisateur).where(Utilisateur.email == payload.email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email déjà utilisé.")
    user = Utilisateur(
        email=payload.email.lower().strip(),
        mot_de_passe_hash=password_hash(payload.mot_de_passe),
        role="Journaliste",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenRead(access_token=create_access_token(user))


@router.post("/login", response_model=TokenRead)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(Utilisateur).where(Utilisateur.email == payload.email.lower().strip()))
    if user is None or not password_matches(payload.mot_de_passe, user.mot_de_passe_hash) or not user.actif:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides.")
    return TokenRead(access_token=create_access_token(user))
