from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

from twitmain.image_processing import build_webp_thumbnail
from twitmain.media_status import MediaProcessingStatus


@shared_task
def generate_avatar_thumbnail(*, user_id):
    user_model = get_user_model()
    user = user_model.objects.filter(pk=user_id).first()
    if user is None:
        return False

    if not user.avatar:
        if user.avatar_thumbnail:
            user.avatar_thumbnail.delete(save=False)
        user.avatar_thumbnail = None
        user.avatar_status = MediaProcessingStatus.NONE
        user.save(update_fields=["avatar_thumbnail", "avatar_status"])
        return True

    try:
        thumbnail_name, thumbnail_content = build_webp_thumbnail(user.avatar)
    except Exception:
        user.avatar_status = MediaProcessingStatus.FAILED
        user.save(update_fields=["avatar_status"])
        return False

    if user.avatar_thumbnail:
        user.avatar_thumbnail.delete(save=False)

    user.avatar_thumbnail.save(thumbnail_name, thumbnail_content, save=False)
    user.avatar_status = MediaProcessingStatus.READY
    user.save(update_fields=["avatar_thumbnail", "avatar_status"])
    return True


@shared_task
def send_welcome_email(*, user_id):
    user_model = get_user_model()
    user = user_model.objects.filter(pk=user_id).first()
    if user is None:
        return False
    if not user.email:
        return False

    send_mail(
        subject="Welcome to n-feed",
        message=(
            f"Hi {user.username}, welcome to n-feed.\n\n"
            "Your account is ready. You can now post tweets, follow users, "
            "use hashtags, and test the API."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
    return True
