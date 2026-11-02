from pydantic import BaseModel, Field


class GeneratedDraft(BaseModel):
    titre: str = Field(min_length=1, max_length=250)
    synthese: str = Field(min_length=1)
    score_credibilite: float = Field(ge=0, le=100, allow_inf_nan=False)
    limites: str = Field(min_length=1)
