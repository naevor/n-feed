import json
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format

from tags.templatetags.tweet_formatting import format_tweet

FEED_GROUP_NAME = "feed_updates"
logger = logging.getLogger(__name__)


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


def comment_payload(comment):
    created_at = timezone.localtime(comment.created_at)
    data = {
        "id": comment.id,
        "tweet_id": comment.tweet_id,
        "content": comment.content,
        "content_html": str(format_tweet(comment.content)),
        "created_at": date_format(created_at, "DATETIME_FORMAT"),
        "user": {
            "id": comment.user_id,
            "username": comment.user.username,
            "profile_url": reverse("users:profile", args=[comment.user.username]),
        },
    }
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))


def broadcast_tweet_created(tweet):
    return _group_send(
        feed_group_name(),
        {
            "type": "tweet.created",
            "payload": tweet_payload(tweet),
        },
    )


def broadcast_comment_created(comment):
    return _group_send(
        feed_group_name(),
        {
            "type": "tweet.comment_created",
            "payload": comment_payload(comment),
        },
    )


def broadcast_tweet_likes_changed(*, tweet_id, likes_count, actor_user_id=None, liked=None):
    payload = {
        "tweet_id": tweet_id,
        "likes_count": likes_count,
    }
    if actor_user_id is not None:
        payload["actor_user_id"] = actor_user_id
    if liked is not None:
        payload["liked"] = liked

    return _group_send(
        feed_group_name(),
        {
            "type": "tweet.likes_changed",
            "payload": payload,
        },
    )


def _group_send(group_name, event):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return False

    try:
        async_to_sync(channel_layer.group_send)(group_name, event)
    except Exception:
        logger.exception("Failed to broadcast feed event to %s", group_name)
        return False
    return True
