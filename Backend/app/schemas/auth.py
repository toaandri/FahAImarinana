from datetime import datetime
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,field_validator
from ..core.rbac import Role,Permission,ROLE_PERMISSIONS


class Credentials(BaseModel):
    model_config=ConfigDict(extra='forbid')
    email: str=Field(min_length=3,max_length=255)
    mot_de_passe: str=Field(min_length=8,max_length=1024)

    @field_validator('email')
    @classmethod
    def normalize_email(cls,value):
        value=value.strip().lower()
        if value.count('@')!=1 or any(char.isspace() for char in value) or not all(value.split('@')):
            raise ValueError('Adresse email invalide.')
        return value

    @field_validator('mot_de_passe')
    @classmethod
    def password_bytes(cls,value):
        if len(value.encode('utf-8'))>4096:
            raise ValueError('Mot de passe trop long.')
        return value


class UserCreate(Credentials):
    invitation_token: str|None=Field(default=None,max_length=256)


class LoginRequest(Credentials):
    pass


class TokenRead(BaseModel):
    access_token: str
    token_type: str='bearer'
    refresh_token: str
    expires_in: int
    refresh_expires_in: int
    session_id: str


class RefreshRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    refresh_token: str=Field(min_length=32,max_length=256)


class InvitationCreate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    email: str=Field(min_length=3,max_length=255)
    role: Role=Role.LECTEUR
    _email=field_validator('email')(Credentials.normalize_email.__func__)

    @field_validator('role')
    @classmethod
    def human_role(cls,value):
        if value==Role.SERVICE_IA:
            raise ValueError('Utiliser la création de compte de service.')
        return value


class AccountUpdate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    role: Role|None=None
    status: Literal['active','suspended','archived']|None=None


class ServiceAccountCreate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    email: str=Field(min_length=3,max_length=255)
    permissions: list[Permission]=Field(min_length=1,max_length=4)
    _email=field_validator('email')(Credentials.normalize_email.__func__)

    @field_validator('permissions')
    @classmethod
    def service_permissions(cls,value):
        if not set(value)<=ROLE_PERMISSIONS[Role.SERVICE_IA]:
            raise ValueError('Permission interdite pour un compte IA.')
        return list(dict.fromkeys(value))


class ServiceLogin(BaseModel):
    model_config=ConfigDict(extra='forbid')
    client_id: str=Field(max_length=255)
    client_secret: str=Field(min_length=32,max_length=256)


class PasswordChange(BaseModel):
    model_config=ConfigDict(extra='forbid')
    current_password: str=Field(max_length=1024)
    new_password: str=Field(min_length=8,max_length=1024)


class AccountRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: int
    email: str
    role: str
    account_type: str
    status: str
    newsroom_id: int
    dataset: str


class SessionRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime|None
    user_agent: str
