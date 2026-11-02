from fastapi import APIRouter,Depends,Request,Response,status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ....database import get_db
from ....core.permissions import current_user
from ....core.rbac import permissions_for
from ....models import User,AuthSession
from ....schemas.auth import (LoginRequest,TokenRead,UserCreate,RefreshRequest,ServiceLogin,
    AccountRead,SessionRead,PasswordChange)
from ....services.auth import (register_user,login_user,refresh_tokens,revoke_session,revoke_all,change_password)

router=APIRouter(prefix='/auth',tags=['Authentification'])


def no_store(response):
    response.headers['Cache-Control']='no-store'
    response.headers['Pragma']='no-cache'


@router.post('/register',response_model=TokenRead,status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate,request: Request,response: Response,db: Session=Depends(get_db)):
    no_store(response)
    return register_user(db,payload,user_agent=request.headers.get('user-agent',''))


@router.post('/login',response_model=TokenRead)
def login(payload: LoginRequest,request: Request,response: Response,db: Session=Depends(get_db)):
    no_store(response)
    return login_user(db,payload,user_agent=request.headers.get('user-agent',''))


@router.post('/service-token',response_model=TokenRead)
def service_login(payload: ServiceLogin,request: Request,response: Response,db: Session=Depends(get_db)):
    no_store(response)
    return login_user(db,payload,service=True,user_agent=request.headers.get('user-agent',''))


@router.post('/refresh',response_model=TokenRead)
def refresh(payload: RefreshRequest,response: Response,db: Session=Depends(get_db)):
    no_store(response)
    return refresh_tokens(db,payload.refresh_token)


@router.get('/me')
def me(user: User=Depends(current_user)):
    return {**AccountRead.model_validate(user).model_dump(),'permissions':sorted(permissions_for(user))}


@router.get('/sessions',response_model=list[SessionRead])
def sessions(db: Session=Depends(get_db),user: User=Depends(current_user)):
    return list(db.scalars(select(AuthSession).where(AuthSession.user_id==user.id).order_by(AuthSession.created_at.desc())))


@router.delete('/sessions/{session_id}',status_code=204)
def revoke(session_id: str,db: Session=Depends(get_db),user: User=Depends(current_user)):
    revoke_session(db,user,session_id)


@router.post('/logout',status_code=204)
def logout(db: Session=Depends(get_db),user: User=Depends(current_user)):
    revoke_session(db,user,db.info['auth_session_id'])


@router.post('/logout-all',status_code=204)
def logout_all(db: Session=Depends(get_db),user: User=Depends(current_user)):
    revoke_all(db,user)


@router.post('/password',status_code=204)
def password(payload: PasswordChange,db: Session=Depends(get_db),user: User=Depends(current_user)):
    change_password(db,user,payload)
