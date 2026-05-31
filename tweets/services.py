from django.db import transaction

from .models import Tweet
from .realtime import (
    broadcast_comment_created,
    broadcast_tweet_created,
    broadcast_tweet_likes_changed,
)


def _broadcast_tweet_created_after_commit(tweet):
    transaction.on_commit(lambda: broadcast_tweet_created(tweet))


def _broadcast_tweet_likes_changed_after_commit(*, tweet, actor_user_id, liked):
    tweet_id = tweet.id

    def broadcast():
        tweet = Tweet.objects.filter(pk=tweet_id).first()
        if tweet is None:
            return
        likes_count = tweet.likes.count()
        broadcast_tweet_likes_changed(
            tweet_id=tweet_id,
            likes_count=likes_count,
            actor_user_id=actor_user_id,
            liked=liked,
        )

    transaction.on_commit(broadcast)


def _broadcast_comment_created_after_commit(comment):
    transaction.on_commit(lambda: broadcast_comment_created(comment))


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
        _broadcast_tweet_likes_changed_after_commit(
            tweet=tweet,
            actor_user_id=user.id,
            liked=False,
        )
        return False
    tweet.likes.add(user)
    _broadcast_tweet_likes_changed_after_commit(
        tweet=tweet,
        actor_user_id=user.id,
        liked=True,
    )
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
    _broadcast_comment_created_after_commit(comment)
    return comment
