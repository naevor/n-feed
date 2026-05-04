from django.db.models.signals import post_save
from django.dispatch import receiver

from tweets.models import Tweet

from .services import attach_tags_to_tweet


@receiver(post_save, sender=Tweet)
def sync_tweet_tags(sender, instance, **kwargs):
    attach_tags_to_tweet(instance)
