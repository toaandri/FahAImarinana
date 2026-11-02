from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator
from .articles import PublishRequest
from .drafts import DraftRead


class DraftUpdate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    expected_version: int=Field(ge=1)
    titre_suggere: str|None=Field(default=None,min_length=1,max_length=250)
    synthese_ia: str|None=Field(default=None,min_length=1,max_length=100000)

    @model_validator(mode='after')
    def content_required(self):
        if self.titre_suggere is None and self.synthese_ia is None:
            raise ValueError('Un contenu de brouillon est requis.')
        return self


class DraftVersionRead(DraftRead):
    version: int
    validated_version: int|None
    validated_by_id: int|None
    review_notes: str


class ValidateDraftRequest(PublishRequest):
    expected_version: int=Field(ge=1)


class ReviewDraftRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    expected_version: int=Field(ge=1)
    decision: Literal['reviewed','changes_requested','rejected']
    notes: str=Field(min_length=1,max_length=5000)


class CorrectionRequest(PublishRequest):
    reason: str=Field(min_length=1,max_length=5000)


class WithdrawalRequest(BaseModel):
    reason: str=Field(min_length=1,max_length=5000)
