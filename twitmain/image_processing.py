from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image


def build_webp_thumbnail(source_file, *, max_size=None):
    size = max_size or settings.MEDIA_THUMBNAIL_MAX_SIZE
    source_file.open("rb")

    try:
        with Image.open(source_file) as image:
            image.seek(0)
            image.thumbnail((size, size), Image.Resampling.LANCZOS)
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")

            output = BytesIO()
            image.save(output, format="WEBP", quality=85, method=6)
    finally:
        source_file.close()

    source_name = Path(source_file.name)
    thumbnail_name = f"{source_name.stem}-thumb.webp"
    return thumbnail_name, ContentFile(output.getvalue())
