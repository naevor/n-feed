from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone

from tweets.selectors import feed_qs

from .models import Tag

TRENDING_TAGS_CACHE_KEY = 'trending_tags_v1'
TRENDING_TAGS_TTL_SECONDS = 300
TRENDING_TAGS_CACHE_LIMIT = 50


def trending_tags(*, limit=10):
    cached = cache.get(TRENDING_TAGS_CACHE_KEY)
    if cached is not None:
        return cached[:limit]

    since = timezone.now() - timedelta(hours=24)
    tags = (
        Tag.objects
        .annotate(
            tweet_count=Count(
                'tweets',
                filter=Q(tweets__created_at__gte=since),
                distinct=True,
            )
        )
        .filter(tweet_count__gt=0)
        .order_by('-tweet_count', 'name')[:TRENDING_TAGS_CACHE_LIMIT]
    )
    result = [
        {'name': tag.name, 'tweet_count': tag.tweet_count}
        for tag in tags
    ]
    cache.set(TRENDING_TAGS_CACHE_KEY, result, TRENDING_TAGS_TTL_SECONDS)
    return result


def tagged_tweets_qs(*, name, user=None):
    return feed_qs(user=user).filter(tags__name=name.lower())
