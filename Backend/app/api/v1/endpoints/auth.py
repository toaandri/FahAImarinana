from fastapi import APIRouter,Depends,Request,Response,status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ....database import get_db
from ....core.permissions import current_user
from ....core.rbac import permissions_for
from ....models import User,AuthSession,Publication,MediaAnalysis,Contribution
from ....schemas.auth import (LoginRequest,TokenRead,UserCreate,RefreshRequest,ServiceLogin,
    AccountRead,SessionRead,PasswordChange,PasswordResetRequest,PasswordReset,ProfileUpdate)
from ....services.auth import (register_user,login_user,refresh_tokens,revoke_session,revoke_all,change_password,update_profile,
request_password_reset,reset_password)
from ....schemas.profile import ProfilePhotoRead, ProfilePhotoUpdate, ProfileLanguage
from ....services.profile import read_profile_photo, save_profile_photo

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

@router.post('/password/forgot')
def forgot_password(payload: PasswordResetRequest, response: Response, db: Session=Depends(get_db)):
    no_store(response)
    return request_password_reset(db, payload)

@router.post('/password/reset')
def reset(payload: PasswordReset, response: Response, db: Session=Depends(get_db)):
    no_store(response)
    return reset_password(db, payload)


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
    return {**AccountRead.model_validate(user).model_dump(),'permissions':sorted(permissions_for(user)),
            'response_language': user.response_language}

@router.get('/me/stats')
def stats(db: Session=Depends(get_db), user: User=Depends(current_user)):
    publications = db.scalar(select(func.count(Publication.id)).where(
        Publication.id_journaliste_validateur == user.id,
        Publication.newsroom_id == user.newsroom_id, Publication.dataset == user.dataset,
    )) or 0
    verifications = db.scalar(select(func.count(MediaAnalysis.id)).where(
        MediaAnalysis.utilisateur_id == user.id,
        MediaAnalysis.newsroom_id == user.newsroom_id, MediaAnalysis.dataset == user.dataset,
    )) or 0
    contributions = db.scalar(select(func.count(Contribution.id)).where(
        Contribution.submitted_by_id == user.id,
        Contribution.newsroom_id == user.newsroom_id, Contribution.dataset == user.dataset,
    )) or 0
    return {'publications': publications, 'verifications': verifications,
            'credibility': None, 'contributions': contributions}

@router.get('/notifications')
def notifications(db: Session=Depends(get_db), user: User=Depends(current_user)):
    items = []
    if user.created_at:
        items.append({'id': 'account-created', 'title': 'Compte actif',
                      'message': 'Votre compte FAH AI MARINANA est prêt à être utilisé.',
                      'created_at': user.created_at.isoformat(), 'read': True})
    recent = db.scalars(select(Contribution).where(
        Contribution.submitted_by_id == user.id,
        Contribution.newsroom_id == user.newsroom_id, Contribution.dataset == user.dataset,
    ).order_by(Contribution.created_at.desc()).limit(10))
    for contribution in recent:
        items.append({'id': f'contribution-{contribution.id}', 'title': 'Contribution reçue',
                      'message': f'Votre contribution est {contribution.status}.',
                      'created_at': contribution.created_at.isoformat(), 'read': contribution.status != 'submitted'})
    return items


@router.patch('/me/language', response_model=ProfileLanguage)
def update_language(payload: ProfileLanguage, response: Response,
                    db: Session = Depends(get_db), user: User = Depends(current_user)):
    no_store(response)
    user.response_language = payload.language
    db.commit()
    return payload


@router.get('/me/photo', response_model=ProfilePhotoRead)
def profile_photo(response: Response, user: User = Depends(current_user)):
    no_store(response)
    return read_profile_photo(user)


@router.put('/me/photo', response_model=ProfilePhotoRead)
def update_profile_photo(payload: ProfilePhotoUpdate, response: Response,
                         db: Session = Depends(get_db), user: User = Depends(current_user)):
    no_store(response)
    return save_profile_photo(db, user, payload.image_base64)


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

@router.patch('/me',response_model=AccountRead)
def profile(payload: ProfileUpdate, response: Response, db: Session=Depends(get_db), user: User=Depends(current_user)):
    no_store(response)
    return update_profile(db,user,payload)
