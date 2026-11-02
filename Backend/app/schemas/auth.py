from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class UserCreate(BaseModel):
    email: str
    mot_de_passe: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: str
    mot_de_passe: str = Field(min_length=8)


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
