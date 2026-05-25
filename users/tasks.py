from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail


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
