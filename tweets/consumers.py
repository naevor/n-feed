from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .realtime import feed_group_name


class FeedConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.group_name = feed_group_name()
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        group_name = getattr(self, "group_name", None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def tweet_created(self, event):
        await self.send_json(
            {
                "type": "tweet.created",
                "tweet": event["payload"],
            }
        )

    async def tweet_likes_changed(self, event):
        await self.send_json(
            {
                "type": "tweet.likes_changed",
                "tweet": event["payload"],
            }
        )
