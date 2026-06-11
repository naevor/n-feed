from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from twitmain.media_files import file_field_name, schedule_file_delete

from .models import Tweet


@receiver(pre_save, sender=Tweet)
def remember_old_tweet_media(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_media_name = ""
        return

    old_tweet = sender.objects.filter(pk=instance.pk).only("media").first()
    instance._old_media_name = file_field_name(old_tweet.media) if old_tweet else ""


@receiver(post_save, sender=Tweet)
def delete_replaced_tweet_media(sender, instance, **kwargs):
    old_name = getattr(instance, "_old_media_name", "")
    new_name = file_field_name(instance.media)
    if old_name and old_name != new_name:
        schedule_file_delete(
            instance.media.storage,
            old_name,
            reason="tweet_media_replaced",
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
