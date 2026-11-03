"""Private profile images stored as bytes, never as device-local file paths."""
import base64
import binascii

from sqlalchemy.orm import Session

from ..core.errors import ValidationDomainError
from ..models import User
from ..schemas.profile import MAX_PHOTO_BYTES


def _mime_type(raw: bytes) -> str:
    if raw.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    if raw.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    if len(raw) >= 12 and raw[:4] == b'RIFF' and raw[8:12] == b'WEBP':
        return 'image/webp'
    raise ValidationDomainError('Choisissez une photo JPEG, PNG ou WebP.')


def read_profile_photo(user: User) -> dict:
    if user.profile_photo is None:
        return {'photo': None}
    raw = user.profile_photo
    return {'photo': f'data:{_mime_type(raw)};base64,{base64.b64encode(raw).decode("ascii")}'}


def save_profile_photo(db: Session, user: User, image_base64: str) -> dict:
    try:
        raw = base64.b64decode(image_base64, validate=True)
    except (ValueError, binascii.Error):
        raise ValidationDomainError('Encodage de la photo invalide.') from None
    if len(raw) > MAX_PHOTO_BYTES:
        raise ValidationDomainError('La photo dépasse 2 Mio. Choisissez une image plus petite.')
    _mime_type(raw)
    user.profile_photo = raw
    db.commit()
    return read_profile_photo(user)
