from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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


class ResearchAnswer(BaseModel):
    reponse: str
    citations: list[dict[str, Any]]
    chronologie: list[dict[str, Any]]
