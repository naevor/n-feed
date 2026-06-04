import json
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.serializers.json import DjangoJSONEncoder

from .serializers import NotificationSerializer

logger = logging.getLogger(__name__)


def notification_group_name(user_id):
    return f"user_{user_id}_notifications"


def notification_payload(notification):
    data = NotificationSerializer(notification).data
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))


def broadcast_notification(notification):
    return _group_send(
        notification_group_name(notification.recipient_id),
        {
            "type": "notification.created",
            "payload": notification_payload(notification),
        },
    )


def broadcast_unread_count(*, user_id, unread_count):
    return _group_send(
        notification_group_name(user_id),
        {
            "type": "notification.unread_count",
            "payload": {
                "unread_count": unread_count,
            },
        },
    )


def _group_send(group_name, event):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return False

    try:
        async_to_sync(channel_layer.group_send)(group_name, event)
    except Exception:
        logger.exception("Failed to broadcast notification event to %s", group_name)
        return False
    return True
