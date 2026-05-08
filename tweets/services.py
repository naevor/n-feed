from .models import Tweet


def create_tweet(*, user, form=None, content=None, media=None):
    if form is not None:
        tweet = form.save(commit=False)
        tweet.user = user
        tweet.save()
        return tweet

    if content is None:
        raise ValueError("content is required")
    return Tweet.objects.create(user=user, content=content, media=media)


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
