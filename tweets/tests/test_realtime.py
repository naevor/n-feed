from unittest.mock import patch

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TransactionTestCase, override_settings

from tweets.consumers import FeedConsumer
from tweets.forms import CommentForm
from tweets.models import Tweet
from tweets.realtime import (
    broadcast_comment_created,
    broadcast_tweet_created,
    broadcast_tweet_likes_changed,
    comment_payload,
    feed_group_name,
    tweet_payload,
)
from tweets.services import add_comment, create_tweet, toggle_like

User = get_user_model()


CHANNEL_TEST_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}


class BrokenChannelLayer:
    async def group_send(self, *args, **kwargs):
        raise RuntimeError("channel layer down")


@override_settings(CHANNEL_LAYERS=CHANNEL_TEST_LAYERS)
class TweetRealtimeTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="author", password="testpass123")

    def test_feed_websocket_receives_created_tweet(self):
        tweet = Tweet.objects.create(user=self.user, content="live tweet")
        message = async_to_sync(self._send_feed_event)(
            {
                "type": "tweet.created",
                "payload": tweet_payload(tweet),
            }
        )

        self.assertEqual(message["type"], "tweet.created")
        self.assertEqual(message["tweet"]["content"], "live tweet")
        self.assertEqual(message["tweet"]["user"]["username"], "author")

    def test_feed_websocket_receives_likes_changed(self):
        tweet = Tweet.objects.create(user=self.user, content="live tweet")
        message = async_to_sync(self._send_feed_event)(
            {
                "type": "tweet.likes_changed",
                "payload": {
                    "tweet_id": tweet.id,
                    "likes_count": 3,
                    "actor_user_id": self.user.id,
                    "liked": True,
                },
            }
        )

        self.assertEqual(message["type"], "tweet.likes_changed")
        self.assertEqual(
            message["tweet"],
            {
                "tweet_id": tweet.id,
                "likes_count": 3,
                "actor_user_id": self.user.id,
                "liked": True,
            },
        )

    def test_feed_websocket_receives_comment_created(self):
        tweet = Tweet.objects.create(user=self.user, content="live tweet")
        form = CommentForm({"content": "live comment"})
        self.assertTrue(form.is_valid())
        comment = add_comment(user=self.user, tweet=tweet, form=form)

        message = async_to_sync(self._send_feed_event)(
            {
                "type": "tweet.comment_created",
                "payload": comment_payload(comment),
            }
        )

        self.assertEqual(message["type"], "tweet.comment_created")
        self.assertEqual(message["comment"]["tweet_id"], tweet.id)
        self.assertEqual(message["comment"]["content"], "live comment")
        self.assertIn("content_html", message["comment"])

    def test_create_tweet_broadcasts_after_commit(self):
        with patch("tweets.services.broadcast_tweet_created") as broadcast:
            with transaction.atomic():
                tweet = create_tweet(user=self.user, content="created through service")
                broadcast.assert_not_called()

        broadcast.assert_called_once_with(tweet)

    def test_toggle_like_broadcasts_after_commit(self):
        liker = User.objects.create_user(username="liker", password="testpass123")
        tweet = Tweet.objects.create(user=self.user, content="liked through service")

        with patch("tweets.services.broadcast_tweet_likes_changed") as broadcast:
            with transaction.atomic():
                liked = toggle_like(user=liker, tweet=tweet)
                broadcast.assert_not_called()

        self.assertTrue(liked)
        broadcast.assert_called_once_with(
            tweet_id=tweet.id,
            likes_count=1,
            actor_user_id=liker.id,
            liked=True,
        )

    def test_add_comment_broadcasts_after_commit(self):
        tweet = Tweet.objects.create(user=self.user, content="comment target")
        form = CommentForm({"content": "created through service"})
        self.assertTrue(form.is_valid())

        with patch("tweets.services.broadcast_comment_created") as broadcast:
            with transaction.atomic():
                comment = add_comment(user=self.user, tweet=tweet, form=form)
                broadcast.assert_not_called()

        broadcast.assert_called_once_with(comment)

    def test_feed_broadcasts_return_false_when_channel_layer_fails(self):
        tweet = Tweet.objects.create(user=self.user, content="channel outage")
        form = CommentForm({"content": "comment during outage"})
        self.assertTrue(form.is_valid())
        comment = add_comment(user=self.user, tweet=tweet, form=form)

        with patch("tweets.realtime.get_channel_layer", return_value=BrokenChannelLayer()):
            self.assertFalse(broadcast_tweet_created(tweet))
            self.assertFalse(broadcast_comment_created(comment))
            self.assertFalse(
                broadcast_tweet_likes_changed(
                    tweet_id=tweet.id,
                    likes_count=1,
                    actor_user_id=self.user.id,
                    liked=True,
                )
            )

    async def _send_feed_event(self, event):
        communicator = WebsocketCommunicator(
            FeedConsumer.as_asgi(),
            "/ws/feed/",
        )

        connected, _ = await communicator.connect()
        assert connected

        channel_layer = get_channel_layer()
        await channel_layer.group_send(feed_group_name(), event)

        message = await communicator.receive_json_from(timeout=1)
        await communicator.disconnect()
        return message
