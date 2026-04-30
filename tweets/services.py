from .models import Tweet, Comment


def create_tweet(*, user, form):
    tweet = form.save(commit=False)
    tweet.user = user
    tweet.save()
    return tweet


def update_tweet(*, user, tweet, form):
    if tweet.user_id != user.id:
        raise PermissionError("not the owner")
    return form.save()


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
