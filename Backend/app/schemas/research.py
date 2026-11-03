from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from ..utils.languages import Language


class ResearchRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2_000)


class ChatSessionCreate(BaseModel):
    titre: str = Field(default="Investigation", min_length=1, max_length=250)


class ChatSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    utilisateur_id: int
    titre: str
    cree_le: datetime
    mise_a_jour_le: datetime


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: str
    contenu: str
    citations: list[dict[str, Any]]
    horodatage: datetime


class ResearchQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=2_000)
    session_id: int | None = None
    language: Language | None = None


class ResearchAnswer(BaseModel):
    reponse: str
    citations: list[dict[str, Any]]
    chronologie: list[dict[str, Any]]


class TranslationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=12000)
    target_language: Literal['fr', 'mg']


class TranslationRead(BaseModel):
    text: str
    language: Literal['fr', 'mg']
    provider: str
