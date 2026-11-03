from pydantic import BaseModel, ConfigDict, Field


class PrecomputeRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    article_url: str = Field(min_length=1, max_length=2000)
