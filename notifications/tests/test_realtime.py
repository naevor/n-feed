from unittest.mock import patch

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import transaction
from django.test import TransactionTestCase, override_settings

from notifications.consumers import NotificationConsumer
from notifications.models import Notification
from notifications.realtime import notification_group_name, notification_payload
from notifications.services import create_notification
from tweets.models import Tweet

User = get_user_model()


CHANNEL_TEST_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}


@override_settings(CHANNEL_LAYERS=CHANNEL_TEST_LAYERS)
class NotificationRealtimeTests(TransactionTestCase):
    def setUp(self):
        self.recipient = User.objects.create_user(username="recipient", password="testpass123")
        self.actor = User.objects.create_user(username="actor", password="testpass123")
        self.tweet = Tweet.objects.create(user=self.recipient, content="hello")

    def test_anonymous_websocket_is_rejected(self):
        communicator = WebsocketCommunicator(
            NotificationConsumer.as_asgi(),
            "/ws/notifications/",
        )
        communicator.scope["user"] = AnonymousUser()

        connected, _ = async_to_sync(communicator.connect)()

        self.assertFalse(connected)

    def test_authenticated_user_receives_created_notification(self):
        notification = Notification.objects.create(
            recipient=self.recipient,
            actor=self.actor,
            kind=Notification.Kind.LIKE,
            tweet=self.tweet,
        )
        payload = notification_payload(notification)

        message = async_to_sync(self._send_notification_event)(payload)

        self.assertEqual(message["type"], "notification.created")
        self.assertEqual(message["notification"]["kind"], Notification.Kind.LIKE)
        self.assertEqual(message["notification"]["actor"]["username"], self.actor.username)

    def test_create_notification_broadcasts_when_notification_is_new(self):
        with patch("notifications.services.broadcast_notification") as broadcast:
            create_notification(
                recipient=self.recipient,
                actor=self.actor,
                kind=Notification.Kind.LIKE,
                tweet=self.tweet,
            )

        broadcast.assert_called_once()

    def test_create_notification_broadcast_waits_for_transaction_commit(self):
        with patch("notifications.services.broadcast_notification") as broadcast:
            with transaction.atomic():
                create_notification(
                    recipient=self.recipient,
                    actor=self.actor,
                    kind=Notification.Kind.LIKE,
                    tweet=self.tweet,
                )
                broadcast.assert_not_called()

        broadcast.assert_called_once()

    async def _send_notification_event(self, payload):
        communicator = WebsocketCommunicator(
            NotificationConsumer.as_asgi(),
            "/ws/notifications/",
        )
        communicator.scope["user"] = self.recipient

        connected, _ = await communicator.connect()
        assert connected

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            notification_group_name(self.recipient.id),
            {
                "type": "notification.created",
                "payload": payload,
            },
        )

        message = await communicator.receive_json_from(timeout=1)
        await communicator.disconnect()
        return message
