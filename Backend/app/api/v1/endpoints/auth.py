from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from ....database import get_db
from ....schemas import LoginRequest, TokenRead, UserCreate
from ....services.auth import register_user, login_user

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/register", response_model=TokenRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    return TokenRead(access_token=register_user(db, payload))


@router.post("/login", response_model=TokenRead)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return TokenRead(access_token=login_user(db, payload))
