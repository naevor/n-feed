from channels.generic.websocket import AsyncJsonWebsocketConsumer

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
