from celery import shared_task

from twitmain.image_processing import build_webp_thumbnail
from twitmain.media_files import cleanup_orphan_media
from twitmain.media_status import MediaProcessingStatus

from .models import Tweet


@shared_task
def generate_tweet_media_thumbnail(*, tweet_id):
    tweet = Tweet.objects.filter(pk=tweet_id).first()
    if tweet is None:
        return False

    if not tweet.media:
        if tweet.media_thumbnail:
            tweet.media_thumbnail.delete(save=False)
        tweet.media_thumbnail = None
        tweet.media_status = MediaProcessingStatus.NONE
        tweet.save(update_fields=["media_thumbnail", "media_status"])
        return True

    try:
        thumbnail_name, thumbnail_content = build_webp_thumbnail(tweet.media)
    except Exception:
        tweet.media_status = MediaProcessingStatus.FAILED
        tweet.save(update_fields=["media_status"])
        return False

    if tweet.media_thumbnail:
        tweet.media_thumbnail.delete(save=False)

    tweet.media_thumbnail.save(thumbnail_name, thumbnail_content, save=False)
    tweet.media_status = MediaProcessingStatus.READY
    tweet.save(update_fields=["media_thumbnail", "media_status"])
    return True

@shared_task
def cleanup_orphan_media_task():
    report = cleanup_orphan_media(delete=True)
    return {
        "scanned": report.scanned,
        "orphaned": len(report.orphaned),
        "deleted": len(report.deleted),
    }
