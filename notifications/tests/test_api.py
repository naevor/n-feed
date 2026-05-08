from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from notifications.models import Notification
from tweets.models import Tweet

User = get_user_model()


class NotificationApiTests(APITestCase):
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

    def test_notifications_api_requires_authentication(self):
        response = self.client.get("/api/v1/notifications/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_list_own_notifications(self):
        self.client.force_authenticate(user=self.recipient)

        response = self.client.get("/api/v1/notifications/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["kind"], Notification.Kind.LIKE)

    def test_mark_read_and_mark_all_read(self):
        second = Notification.objects.create(
            recipient=self.recipient,
            actor=self.actor,
            kind=Notification.Kind.FOLLOW,
        )
        self.client.force_authenticate(user=self.recipient)

        mark_one_response = self.client.post(
            f"/api/v1/notifications/{self.notification.id}/mark_read/"
        )
        mark_all_response = self.client.post("/api/v1/notifications/mark_all_read/")

        self.assertEqual(mark_one_response.status_code, status.HTTP_200_OK)
        self.assertEqual(mark_all_response.status_code, status.HTTP_200_OK)
        self.assertTrue(mark_one_response.data["read"])
        self.assertEqual(mark_all_response.data["marked"], 1)
        self.notification.refresh_from_db()
        second.refresh_from_db()
        self.assertTrue(self.notification.is_read)
        self.assertTrue(second.is_read)
