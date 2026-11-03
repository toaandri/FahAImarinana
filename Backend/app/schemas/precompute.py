from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class PrecomputeRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    article_url: HttpUrl = Field(max_length=2000)
