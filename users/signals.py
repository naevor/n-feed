from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from twitmain.media_files import file_field_name, schedule_file_delete

from .models import CustomUser


@receiver(pre_save, sender=CustomUser)
def remember_old_avatar(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_avatar_name = ""
        return

    old_user = sender.objects.filter(pk=instance.pk).only("avatar").first()
    instance._old_avatar_name = file_field_name(old_user.avatar) if old_user else ""


@receiver(post_save, sender=CustomUser)
def delete_replaced_avatar(sender, instance, **kwargs):
    old_name = getattr(instance, "_old_avatar_name", "")
    new_name = file_field_name(instance.avatar)
    if old_name and old_name != new_name:
        schedule_file_delete(
            instance.avatar.storage,
            old_name,
            reason="avatar_replaced",
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
