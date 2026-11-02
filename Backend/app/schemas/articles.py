from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ArticlePublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titre_final: str
    corps_article: str
    categorie: str
    statut_verification: str
    horodatage_validation: datetime
    contenu_optimise_sms: str


class PublishRequest(BaseModel):
    titre_final: str = Field(min_length=1, max_length=250)
    corps_article: str = Field(min_length=1)
    categorie: str = Field(min_length=1, max_length=50)
    statut_verification: Literal["Vrai", "Faux", "Trompeur"]
    contenu_optimise_sms: str = Field(min_length=1, max_length=480)
