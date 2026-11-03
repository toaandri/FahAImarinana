"""Bounded private video input and non-editorial Gemini observations."""
import base64
import binascii
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

MAX_VIDEO_BYTES = 4 * 1024 * 1024
MAX_BASE64_CHARS = 4 * ((MAX_VIDEO_BYTES + 2) // 3)
REVIEW_NOTICE = 'Pré-analyse visuelle IA : contexte et affirmations à vérifier par un journaliste. Aucune validation éditoriale.'


class ImageAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    image_base64: str = Field(min_length=16, max_length=MAX_BASE64_CHARS, repr=False)

    @field_validator('image_base64')
    @classmethod
    def valid_image(cls, value):
        from ..core.media import detect_media_type
        try:
            raw = base64.b64decode(value, validate=True)
        except (ValueError, binascii.Error):
            raise ValueError('Encodage image base64 invalide.') from None
        if len(raw) > MAX_VIDEO_BYTES or detect_media_type(raw) not in ('image/jpeg', 'image/png', 'image/gif', 'image/webp'):
            raise ValueError('Une image JPEG, PNG, GIF ou WebP de 4 Mio maximum est requise.')
        return value


class VideoClipRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    capture_id: UUID
    sequence: int = Field(ge=1, le=100000)
    captured_at: AwareDatetime
    duration_seconds: float = Field(gt=0, le=10)
    mime_type: Literal['video/mp4', 'video/quicktime'] = 'video/mp4'
    video_base64: str = Field(min_length=16, max_length=MAX_BASE64_CHARS, repr=False)
    language: Literal['fr', 'mg', 'en'] = 'fr'
    case_id: int | None = Field(default=None, gt=0)

    @field_validator('video_base64')
    @classmethod
    def valid_video(cls, value):
        try:
            raw = base64.b64decode(value, validate=True)
        except (ValueError, binascii.Error):
            raise ValueError('Encodage vidéo base64 invalide.') from None
        if len(raw) > MAX_VIDEO_BYTES:
            raise ValueError('Le clip dépasse 4 Mio.')
        # Modern camera MP4/MOV containers. Gemini still validates the actual media.
        if len(raw) < 16 or raw[4:8] != b'ftyp':
            raise ValueError('Un clip MP4/MOV de la caméra est requis.')
        return value


class VideoObservation(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False, str_strip_whitespace=True)
    time_seconds: float = Field(ge=0, le=10)
    description: str = Field(min_length=1, max_length=2000)


class VideoAnalysisResult(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=250)
    summary: str = Field(min_length=1, max_length=10000)
    observations: list[VideoObservation] = Field(max_length=20)
    limitations: list[str] = Field(min_length=1, max_length=20)
    questions_to_verify: list[str] = Field(max_length=10)

    @field_validator('limitations', 'questions_to_verify')
    @classmethod
    def bounded_items(cls, values):
        if any(not value.strip() or len(value) > 2000 for value in values):
            raise ValueError('Chaque limite/question doit être explicite et bornée.')
        return values


class VideoAnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    capture_key: str | None
    empreinte_sha256: str
    cree_le: datetime
    result: dict | None
    requires_human_review: Literal[True] = True
