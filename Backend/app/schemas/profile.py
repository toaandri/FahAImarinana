from pydantic import BaseModel, ConfigDict, Field

MAX_PHOTO_BYTES = 2 * 1024 * 1024
MAX_PHOTO_BASE64_CHARS = 4 * ((MAX_PHOTO_BYTES + 2) // 3)


class ProfilePhotoUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    image_base64: str = Field(min_length=1, max_length=MAX_PHOTO_BASE64_CHARS, repr=False)


class ProfilePhotoRead(BaseModel):
    photo: str | None
