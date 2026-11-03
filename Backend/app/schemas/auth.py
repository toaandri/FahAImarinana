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
    pass


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
    _email=field_validator('email')(Credentials.normalize_email.__func__)

class AccountUpdate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    status: Literal['active','suspended','archived']


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

class PasswordResetRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    email: str=Field(min_length=3,max_length=255)
    _email=field_validator('email')(Credentials.normalize_email.__func__)

class PasswordReset(BaseModel):
    model_config=ConfigDict(extra='forbid')
    reset_token: str=Field(min_length=20,max_length=2048)
    new_password: str=Field(min_length=8,max_length=1024)

class ProfileUpdate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    name: str=Field(min_length=1,max_length=120)
    email: str=Field(min_length=3,max_length=255)
    _email=field_validator('email')(Credentials.normalize_email.__func__)


class AccountRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: int
    email: str
    name: str
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
