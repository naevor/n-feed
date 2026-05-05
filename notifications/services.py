import re

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Notification

MENTION_RE = re.compile(r'@([A-Za-z0-9_]{2,150})')


def extract_mentions_from_text(text):
    seen = set()
    mentions = []
    for match in MENTION_RE.finditer(text or ''):
        username = match.group(1)
        key = username.lower()
        if key not in seen:
            seen.add(key)
            mentions.append(username)
    return mentions


def create_notification(*, recipient, actor, kind, tweet=None, dedupe=True):
    if not actor or not recipient or actor.pk == recipient.pk:
        return None

    data = {
        'recipient': recipient,
        'actor': actor,
        'kind': kind,
        'tweet': tweet,
    }
    if dedupe:
        notification, _ = Notification.objects.get_or_create(**data)
        return notification
    return Notification.objects.create(**data)


def notify_tweet_mentions(*, tweet):
    usernames = extract_mentions_from_text(tweet.content)
    if not usernames:
        return []

    User = get_user_model()
    users = User.objects.filter(username__in=usernames).exclude(pk=tweet.user_id)
    notifications = []
    with transaction.atomic():
        for recipient in users:
            notification = create_notification(
                recipient=recipient,
                actor=tweet.user,
                kind=Notification.Kind.MENTION,
                tweet=tweet,
            )
            if notification is not None:
                notifications.append(notification)
    return notifications


def mark_notification_read(*, notification):
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])
    return notification


def mark_all_read(*, user):
    return Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)
