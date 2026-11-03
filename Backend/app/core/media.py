import base64
import binascii

MAX_MEDIA_BYTES = 100 * 1024 * 1024
MAX_MEDIA_BASE64_LENGTH = ((MAX_MEDIA_BYTES + 2) // 3) * 4
MAX_CONTRIBUTION_BODY_BYTES = MAX_MEDIA_BASE64_LENGTH + 128 * 1024


class MediaTooLargeError(ValueError):
    pass


def decode_media_base64(value: str) -> bytes:
    try:
        media = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError('Le média encodé est invalide.') from None
    if len(media) > MAX_MEDIA_BYTES:
        raise MediaTooLargeError('Le média dépasse la taille maximale de 100 Mo.')
    return media
