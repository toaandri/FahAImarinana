from fastapi import APIRouter,Depends,Response
from pydantic import BaseModel,ConfigDict,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from ....database import get_db
from ....core.permissions import require_permission
from ....core.rbac import Permission as P
from ....models import User,TechnicalSetting
from ....schemas.auth import AccountRead,InvitationCreate,ServiceAccountCreate,AccountUpdate
from ....services.administration import create_invitation,create_service_account,update_account,set_technical_setting

router=APIRouter(prefix='/admin',tags=['Administration'])


@router.get('/users',response_model=list[AccountRead])
def users(db: Session=Depends(get_db),actor: User=Depends(require_permission(P.USERS_MANAGE))):
    return list(db.scalars(select(User).order_by(User.id).limit(200)))


@router.post('/invitations',status_code=201)
def invite(payload: InvitationCreate,response: Response,db: Session=Depends(get_db),
           actor: User=Depends(require_permission(P.USERS_MANAGE))):
    response.headers['Cache-Control']='no-store'
    return create_invitation(db,actor,payload)


@router.post('/service-accounts',status_code=201)
def service_account(payload: ServiceAccountCreate,response: Response,db: Session=Depends(get_db),
                    actor: User=Depends(require_permission(P.USERS_MANAGE))):
    response.headers['Cache-Control']='no-store'
    return create_service_account(db,actor,payload)


@router.patch('/users/{user_id}',response_model=AccountRead)
def edit_user(user_id: int,payload: AccountUpdate,db: Session=Depends(get_db),
              actor: User=Depends(require_permission(P.USERS_MANAGE))):
    return update_account(db,actor,user_id,payload)


class SettingUpdate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    value: int=Field(ge=1,le=100)


@router.get('/settings')
def settings(db: Session=Depends(get_db),actor: User=Depends(require_permission(P.SETTINGS_MANAGE))):
    return [{'key':setting.key,'value':setting.value} for setting in db.scalars(select(TechnicalSetting))]


@router.put('/settings/{key}')
def update_setting(key: str,payload: SettingUpdate,db: Session=Depends(get_db),
                   actor: User=Depends(require_permission(P.SETTINGS_MANAGE))):
    return set_technical_setting(db,actor,key,payload.value)
