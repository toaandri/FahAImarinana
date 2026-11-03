"""Journalist-assessed source concordance, not a probability of truth."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class AssessedSource(BaseModel):
    model_config = ConfigDict(extra='forbid')
    url: HttpUrl | Annotated[str, Field(pattern=r'^article:[1-9][0-9]{0,9}$')] = Field(max_length=500)
    assessment: Literal['supports', 'contradicts', 'inconclusive']


class CredibilityRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    claim: str = Field(min_length=3, max_length=2000)
    sources: list[AssessedSource] = Field(min_length=1, max_length=10)


class CredibilityResult(BaseModel):
    claim: str
    corroboration_percent: float | None
    supports: int
    contradicts: int
    inconclusive: int
    source_groups: int
    excluded_duplicates: int
    limitation: str
