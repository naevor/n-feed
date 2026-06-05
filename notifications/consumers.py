from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Notification
from .realtime import notification_group_name


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close(code=4401)
            return

        self.group_name = notification_group_name(user.id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json(
            {
                "type": "notification.unread_count",
                "unread_count": await self._unread_count(user.id),
            }
        )

    async def disconnect(self, close_code):
        group_name = getattr(self, "group_name", None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def notification_created(self, event):
        await self.send_json(
            {
                "type": "notification.created",
                "notification": event["payload"],
            }
        )

    async def notification_unread_count(self, event):
        await self.send_json(
            {
                "type": "notification.unread_count",
                "unread_count": event["payload"]["unread_count"],
            }
        )

    @database_sync_to_async
    def _unread_count(self, user_id):
        return Notification.objects.filter(recipient_id=user_id, is_read=False).count()
