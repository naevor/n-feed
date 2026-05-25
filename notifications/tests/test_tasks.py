from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from django_celery_beat.models import PeriodicTask

from notifications.models import Notification
from notifications.tasks import cleanup_old_notifications

User = get_user_model()


class NotificationTaskTests(TestCase):
    def setUp(self):
        self.recipient = User.objects.create_user(username="recipient", password="testpass123")
        self.actor = User.objects.create_user(username="actor", password="testpass123")

    def test_cleanup_old_notifications_deletes_only_stale_records(self):
        old_notification = Notification.objects.create(
            recipient=self.recipient,
            actor=self.actor,
            kind=Notification.Kind.FOLLOW,
        )
        Notification.objects.filter(pk=old_notification.pk).update(
            created_at=timezone.now() - timedelta(days=31)
        )
        fresh_notification = Notification.objects.create(
            recipient=self.recipient,
            actor=self.actor,
            kind=Notification.Kind.LIKE,
        )

        deleted_count = cleanup_old_notifications(days=30)

        self.assertEqual(deleted_count, 1)
        self.assertFalse(Notification.objects.filter(pk=old_notification.pk).exists())
        self.assertTrue(Notification.objects.filter(pk=fresh_notification.pk).exists())

    def test_configure_periodic_tasks_is_idempotent(self):
        call_command("configure_periodic_tasks")
        call_command("configure_periodic_tasks")

        task = PeriodicTask.objects.get(name="cleanup old notifications")
        self.assertEqual(task.task, "notifications.tasks.cleanup_old_notifications")
        self.assertTrue(task.enabled)
