import base64
import binascii

MAX_MEDIA_BYTES = 100 * 1024 * 1024
MAX_MEDIA_BASE64_LENGTH = ((MAX_MEDIA_BYTES + 2) // 3) * 4
MAX_CONTRIBUTION_BODY_BYTES = MAX_MEDIA_BASE64_LENGTH + 128 * 1024


class MediaTooLargeError(ValueError):
    pass


def detect_media_type(media: bytes) -> str | None:
    """Identify common camera/gallery formats when the mobile client omits MIME."""
    if media.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    if media.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    if media.startswith((b'GIF87a', b'GIF89a')):
        return 'image/gif'
    if media[:4] == b'RIFF' and media[8:12] == b'WEBP':
        return 'image/webp'
    if media[4:8] == b'ftyp':
        brand = media[8:12]
        if brand in (b'heic', b'heix', b'hevc', b'hevx', b'mif1', b'msf1'):
            return 'image/heic'
        if brand == b'qt  ':
            return 'video/quicktime'
        return 'video/mp4'
    return None


def decode_media_base64(value: str) -> bytes:
    try:
        media = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError('Le média encodé est invalide.') from None
    if len(media) > MAX_MEDIA_BYTES:
        raise MediaTooLargeError('Le média dépasse la taille maximale de 100 Mo.')
    return media
