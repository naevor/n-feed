import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format

FEED_GROUP_NAME = "feed_updates"


def feed_group_name():
    return FEED_GROUP_NAME


def tweet_payload(tweet):
    created_at = timezone.localtime(tweet.created_at)
    data = {
        "id": tweet.id,
        "slug": tweet.slug,
        "content": tweet.content,
        "media_url": tweet.media.url if tweet.media else "",
        "created_at": date_format(created_at, "DATETIME_FORMAT"),
        "tweet_url": reverse("tweets:tweet_detail", args=[tweet.slug]),
        "user": {
            "id": tweet.user_id,
            "username": tweet.user.username,
            "avatar_url": tweet.user.avatar.url if tweet.user.avatar else "",
            "profile_url": reverse("users:profile", args=[tweet.user.username]),
        },
    }
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))


def broadcast_tweet_created(tweet):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return False

    async_to_sync(channel_layer.group_send)(
        feed_group_name(),
        {
            "type": "tweet.created",
            "payload": tweet_payload(tweet),
        },
    )
    return True
