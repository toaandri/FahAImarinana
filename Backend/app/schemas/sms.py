from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SmsRequest(BaseModel):
    numero_expediteur: str = Field(min_length=5, max_length=30)
    message: str = Field(min_length=1, max_length=500)


class SmsResponse(BaseModel):
    message: str
    statut: str
