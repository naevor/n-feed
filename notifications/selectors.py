from django.shortcuts import get_object_or_404

from .models import Notification


def user_notifications_qs(*, user):
    return (
        Notification.objects.filter(recipient=user)
        .select_related("actor", "tweet", "tweet__user")
        .order_by("-created_at", "-id")
    )


def unread_count(*, user):
    if not user.is_authenticated:
        return 0
    return Notification.objects.filter(recipient=user, is_read=False).count()


def notification_for_user(*, user, pk):
    return get_object_or_404(user_notifications_qs(user=user), pk=pk)
