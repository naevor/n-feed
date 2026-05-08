from django.contrib.auth import get_user_model
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from tweets.models import Comment, Tweet
from users.models import CustomUser

from .models import Notification
from .services import create_notification, notify_tweet_mentions


@receiver(m2m_changed, sender=Tweet.likes.through)
def create_like_notifications(sender, instance, action, pk_set, **kwargs):
    if action != "post_add" or not pk_set:
        return

    user_model = get_user_model()
    for actor in user_model.objects.filter(pk__in=pk_set):
        create_notification(
            recipient=instance.user,
            actor=actor,
            kind=Notification.Kind.LIKE,
            tweet=instance,
        )


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if not created:
        return

    create_notification(
        recipient=instance.tweet.user,
        actor=instance.user,
        kind=Notification.Kind.COMMENT,
        tweet=instance.tweet,
        dedupe=False,
    )


@receiver(m2m_changed, sender=CustomUser.following.through)
def create_follow_notifications(sender, instance, action, reverse, pk_set, **kwargs):
    if action != "post_add" or not pk_set:
        return

    user_model = get_user_model()
    if reverse:
        recipient = instance
        actors = user_model.objects.filter(pk__in=pk_set)
        for actor in actors:
            create_notification(
                recipient=recipient,
                actor=actor,
                kind=Notification.Kind.FOLLOW,
            )
        return

    actor = instance
    recipients = user_model.objects.filter(pk__in=pk_set)
    for recipient in recipients:
        create_notification(
            recipient=recipient,
            actor=actor,
            kind=Notification.Kind.FOLLOW,
        )


@receiver(post_save, sender=Tweet)
def create_mention_notifications(sender, instance, **kwargs):
    notify_tweet_mentions(tweet=instance)
