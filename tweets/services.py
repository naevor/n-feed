from django.db import transaction

from .models import Tweet
from .realtime import broadcast_tweet_created


def _broadcast_tweet_created_after_commit(tweet):
    transaction.on_commit(lambda: broadcast_tweet_created(tweet))


def create_tweet(*, user, form=None, content=None, media=None):
    if form is not None:
        tweet = form.save(commit=False)
        tweet.user = user
        tweet.save()
        _broadcast_tweet_created_after_commit(tweet)
        return tweet

    if content is None:
        raise ValueError("content is required")
    tweet = Tweet.objects.create(user=user, content=content, media=media)
    _broadcast_tweet_created_after_commit(tweet)
    return tweet


def update_tweet(*, user, tweet, form=None, **fields):
    if tweet.user_id != user.id:
        raise PermissionError("not the owner")
    if form is not None:
        return form.save()

    for field in ("content", "media"):
        if field in fields:
            setattr(tweet, field, fields[field])
    tweet.save()
    return tweet


def delete_tweet_by_user(*, user, tweet):
    if tweet.user_id != user.id:
        raise PermissionError("not the owner")
    tweet.delete()


def toggle_like(*, user, tweet):
    if tweet.likes.filter(pk=user.pk).exists():
        tweet.likes.remove(user)
        return False
    tweet.likes.add(user)
    return True


def toggle_bookmark(*, user, tweet):
    if tweet.bookmarks.filter(pk=user.pk).exists():
        tweet.bookmarks.remove(user)
        return False
    tweet.bookmarks.add(user)
    return True


def add_comment(*, user, tweet, form):
    comment = form.save(commit=False)
    comment.user = user
    comment.tweet = tweet
    comment.save()
    return comment
