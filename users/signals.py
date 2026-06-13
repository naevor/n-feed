from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from twitmain.media_files import file_field_name, schedule_file_delete
from twitmain.media_status import MediaProcessingStatus

from .models import CustomUser


@receiver(pre_save, sender=CustomUser)
def remember_old_avatar(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_avatar_name = ""
        instance._old_avatar_thumbnail_name = ""
        return

    old_user = sender.objects.filter(pk=instance.pk).only("avatar", "avatar_thumbnail").first()
    instance._old_avatar_name = file_field_name(old_user.avatar) if old_user else ""
    instance._old_avatar_thumbnail_name = file_field_name(old_user.avatar_thumbnail) if old_user else ""


@receiver(post_save, sender=CustomUser)
def process_avatar_change(sender, instance, **kwargs):
    old_name = getattr(instance, "_old_avatar_name", "")
    old_thumbnail_name = getattr(instance, "_old_avatar_thumbnail_name", "")
    new_name = file_field_name(instance.avatar)
    if old_name == new_name:
        return

    if old_name:
        schedule_file_delete(
            instance.avatar.storage,
            old_name,
            reason="avatar_replaced",
        )

    if old_thumbnail_name:
        schedule_file_delete(
            instance.avatar_thumbnail.storage,
            old_thumbnail_name,
            reason="avatar_thumbnail_replaced",
        )

    if new_name:
        sender.objects.filter(pk=instance.pk).update(
            avatar_thumbnail="",
            avatar_status=MediaProcessingStatus.PENDING,
        )
        instance.avatar_thumbnail = None
        instance.avatar_status = MediaProcessingStatus.PENDING

        def enqueue_thumbnail():
            from .tasks import generate_avatar_thumbnail

            generate_avatar_thumbnail.delay(user_id=instance.pk)

        transaction.on_commit(enqueue_thumbnail)
        return

    sender.objects.filter(pk=instance.pk).update(
        avatar_thumbnail="",
        avatar_status=MediaProcessingStatus.NONE,
    )


@receiver(post_delete, sender=CustomUser)
def delete_removed_avatar(sender, instance, **kwargs):
    name = file_field_name(instance.avatar)
    if name:
        schedule_file_delete(
            instance.avatar.storage,
            name,
            reason="user_deleted",
        )

    thumbnail_name = file_field_name(instance.avatar_thumbnail)
    if thumbnail_name:
        schedule_file_delete(
            instance.avatar_thumbnail.storage,
            thumbnail_name,
            reason="user_deleted",
        )
