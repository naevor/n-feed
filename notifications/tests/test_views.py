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

    def test_mark_read_marks_only_owned_notification(self):
        self.client.login(username="recipient", password="testpass123")

        response = self.client.post(reverse("notifications:mark_read", args=[self.notification.id]))

        self.assertRedirects(response, reverse("notifications:list"))
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_context_processor_exposes_unread_count(self):
        self.client.login(username="recipient", password="testpass123")

        response = self.client.get(reverse("tweets:all_tweets"))

        self.assertEqual(response.context["unread_notifications"], 1)
