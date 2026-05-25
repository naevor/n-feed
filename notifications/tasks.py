from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import Notification


@shared_task
def cleanup_old_notifications(*, days=30):
    cutoff = timezone.now() - timedelta(days=days)
    deleted_count, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
    return deleted_count
