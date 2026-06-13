import logging
import posixpath
from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.db import transaction

logger = logging.getLogger(__name__)

MANAGED_MEDIA_PREFIXES = ("avatars", "tweet_media")


@dataclass(frozen=True)
class OrphanMediaReport:
    scanned: int
    orphaned: list[str]
    deleted: list[str]


def file_field_name(field_file):
    if not field_file:
        return ""
    return field_file.name or ""


def schedule_file_delete(storage, name, *, reason):
    if not name:
        return

    def delete_file():
        try:
            if storage.exists(name):
                storage.delete(name)
                logger.info(
                    "Deleted media file",
                    extra={"media_file": name, "media_delete_reason": reason},
                )
        except Exception:
            logger.exception(
                "Failed to delete media file",
                extra={"media_file": name, "media_delete_reason": reason},
            )

    transaction.on_commit(delete_file)


def collect_referenced_media_names():
    from tweets.models import Tweet

    user_model = get_user_model()
    names = set()
    names.update(
        name
        for name in user_model.objects.exclude(avatar="").values_list("avatar", flat=True)
        if name
    )
    names.update(
        name
        for name in user_model.objects.exclude(avatar_thumbnail="").values_list(
            "avatar_thumbnail", flat=True
        )
        if name
    )
    names.update(
        name
        for name in Tweet.objects.exclude(media="").values_list("media", flat=True)
        if name
    )
    names.update(
        name
        for name in Tweet.objects.exclude(media_thumbnail="").values_list(
            "media_thumbnail", flat=True
        )
        if name
    )
    return names


def iter_managed_media_files():
    for prefix in MANAGED_MEDIA_PREFIXES:
        yield from _iter_storage_files(prefix)


def cleanup_orphan_media(*, delete=False):
    referenced_names = collect_referenced_media_names()
    media_names = sorted(set(iter_managed_media_files()))
    orphaned = [name for name in media_names if name not in referenced_names]
    deleted = []

    if delete:
        for name in orphaned:
            default_storage.delete(name)
            deleted.append(name)
            logger.info("Deleted orphan media file", extra={"media_file": name})

    return OrphanMediaReport(
        scanned=len(media_names),
        orphaned=orphaned,
        deleted=deleted,
    )


def _iter_storage_files(prefix):
    try:
        directories, files = default_storage.listdir(prefix)
    except FileNotFoundError:
        return
    except OSError:
        logger.warning("Cannot list media prefix", extra={"media_prefix": prefix})
        return

    for filename in files:
        yield posixpath.join(prefix, filename)

    for directory in directories:
        yield from _iter_storage_files(posixpath.join(prefix, directory))
