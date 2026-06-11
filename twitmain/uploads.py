import logging
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/webp",
}
ALLOWED_IMAGE_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".png", ".webp"}
logger = logging.getLogger(__name__)


def validate_avatar_upload(file):
    validate_image_upload(
        file,
        max_size=settings.MAX_AVATAR_UPLOAD_SIZE,
        label="Avatar",
    )


def validate_tweet_media_upload(file):
    validate_image_upload(
        file,
        max_size=settings.MAX_TWEET_MEDIA_UPLOAD_SIZE,
        label="Tweet media",
    )


def validate_image_upload(file, *, max_size, label):
    if not file:
        return

    if file.size > max_size:
        _reject_upload(label, f"{label} cannot be larger than {_format_size(max_size)}.")

    extension = Path(file.name or "").suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        _reject_upload(label, f"{label} must be an image file: GIF, JPEG, PNG, or WebP.")

    content_type = getattr(file, "content_type", "")
    if content_type and content_type.lower() not in ALLOWED_IMAGE_CONTENT_TYPES:
        _reject_upload(label, f"{label} must use a supported image content type.")

    if not _has_image_dimensions(file):
        _reject_upload(label, f"{label} must be a valid image.")


def _has_image_dimensions(file):
    position = None
    try:
        position = file.tell()
    except (AttributeError, OSError):
        pass

    try:
        return bool(get_image_dimensions(file))
    except Exception:
        return False
    finally:
        if position is not None:
            try:
                file.seek(position)
            except (AttributeError, OSError):
                pass


def _format_size(size):
    return f"{size // (1024 * 1024)} MB"


def _reject_upload(label, message):
    logger.warning("Rejected upload: %s", message, extra={"upload_label": label})
    raise ValidationError(message)
