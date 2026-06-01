from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notifications.models import Notification
from tweets.models import Tweet

User = get_user_model()


class NotificationViewTests(TestCase):
    def setUp(self):
        self.recipient = User.objects.create_user(username="recipient", password="testpass123")
        self.actor = User.objects.create_user(username="actor", password="testpass123")
        self.tweet = Tweet.objects.create(user=self.recipient, content="hello")
        self.notification = Notification.objects.create(
            recipient=self.recipient,
            actor=self.actor,
            kind=Notification.Kind.LIKE,
            tweet=self.tweet,
        )

    def test_notification_list_requires_login(self):
        response = self.client.get(reverse("notifications:list"))

        self.assertEqual(response.status_code, 302)

    def test_notification_list_shows_only_current_user_notifications(self):
        other = User.objects.create_user(username="other", password="testpass123")
        Notification.objects.create(
            recipient=other,
            actor=self.actor,
            kind=Notification.Kind.FOLLOW,
        )
        self.client.login(username="recipient", password="testpass123")

        response = self.client.get(reverse("notifications:list"))

        self.assertContains(response, "liked your tweet")
        self.assertNotContains(response, "followed you")

    def test_notification_list_exposes_async_controls(self):
        self.client.login(username="recipient", password="testpass123")

        response = self.client.get(reverse("notifications:list"))

        self.assertContains(response, "data-notification-list")
        self.assertContains(response, f'data-notification-id="{self.notification.id}"')
        self.assertContains(response, 'data-notification-action="mark-read"')
        self.assertContains(response, 'data-notification-action="mark-all-read"')

    def test_mark_read_marks_only_owned_notification(self):
        self.client.login(username="recipient", password="testpass123")

        response = self.client.post(reverse("notifications:mark_read", args=[self.notification.id]))

        self.assertRedirects(response, reverse("notifications:list"))
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_read_returns_json_for_async_request(self):
        self.client.login(username="recipient", password="testpass123")

        response = self.client.post(
            reverse("notifications:mark_read", args=[self.notification.id]),
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "notification_id": self.notification.id,
                "is_read": True,
                "unread_count": 0,
            },
        )

    def test_mark_all_read_returns_json_for_async_request(self):
        Notification.objects.create(
            recipient=self.recipient,
            actor=self.actor,
            kind=Notification.Kind.COMMENT,
            tweet=self.tweet,
        )
        self.client.login(username="recipient", password="testpass123")

        response = self.client.post(
            reverse("notifications:mark_all_read"),
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"marked_count": 2, "unread_count": 0})

    def test_context_processor_exposes_unread_count(self):
        self.client.login(username="recipient", password="testpass123")

        response = self.client.get(reverse("tweets:all_tweets"))

        self.assertEqual(response.context["unread_notifications"], 1)

    def test_authenticated_layout_loads_realtime_notification_client(self):
        self.client.login(username="recipient", password="testpass123")

        response = self.client.get(reverse("tweets:all_tweets"))

        self.assertContains(response, "data-notification-badge")
        self.assertContains(response, "notifications.js")
