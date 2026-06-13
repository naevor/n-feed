from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from twitmain.media_files import file_field_name, schedule_file_delete
from twitmain.media_status import MediaProcessingStatus

from .models import Tweet


@receiver(pre_save, sender=Tweet)
def remember_old_tweet_media(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_media_name = ""
        instance._old_media_thumbnail_name = ""
        return

    old_tweet = sender.objects.filter(pk=instance.pk).only("media", "media_thumbnail").first()
    instance._old_media_name = file_field_name(old_tweet.media) if old_tweet else ""
    instance._old_media_thumbnail_name = file_field_name(old_tweet.media_thumbnail) if old_tweet else ""


@receiver(post_save, sender=Tweet)
def process_tweet_media_change(sender, instance, **kwargs):
    old_name = getattr(instance, "_old_media_name", "")
    old_thumbnail_name = getattr(instance, "_old_media_thumbnail_name", "")
    new_name = file_field_name(instance.media)
    if old_name == new_name:
        return

    if old_name:
        schedule_file_delete(
            instance.media.storage,
            old_name,
            reason="tweet_media_replaced",
        )

    if old_thumbnail_name:
        schedule_file_delete(
            instance.media_thumbnail.storage,
            old_thumbnail_name,
            reason="tweet_media_thumbnail_replaced",
        )

    if new_name:
        sender.objects.filter(pk=instance.pk).update(
            media_thumbnail="",
            media_status=MediaProcessingStatus.PENDING,
        )
        instance.media_thumbnail = None
        instance.media_status = MediaProcessingStatus.PENDING

        def enqueue_thumbnail():
            from .tasks import generate_tweet_media_thumbnail

            generate_tweet_media_thumbnail.delay(tweet_id=instance.pk)

        transaction.on_commit(enqueue_thumbnail)
        return

    sender.objects.filter(pk=instance.pk).update(
        media_thumbnail="",
        media_status=MediaProcessingStatus.NONE,
    )


@receiver(post_delete, sender=Tweet)
def delete_removed_tweet_media(sender, instance, **kwargs):
    name = file_field_name(instance.media)
    if name:
        schedule_file_delete(
            instance.media.storage,
            name,
            reason="tweet_deleted",
        )

    thumbnail_name = file_field_name(instance.media_thumbnail)
    if thumbnail_name:
        schedule_file_delete(
            instance.media_thumbnail.storage,
            thumbnail_name,
            reason="tweet_deleted",
        )
