from django.contrib.auth import get_user_model
from django.db.models import BooleanField, Count, Exists, OuterRef, Prefetch, Value
from django.shortcuts import get_object_or_404

from .models import Comment, Tweet


def _base_tweet_qs(user=None):
    qs = (
        Tweet.objects
        .select_related('user')
        .annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True),
        )
    )
    if user is not None and user.is_authenticated:
        User = get_user_model()
        qs = qs.annotate(
            is_liked=Exists(User.objects.filter(liked_tweets=OuterRef('pk'), pk=user.pk)),
            is_bookmarked=Exists(User.objects.filter(bookmarked_tweets=OuterRef('pk'), pk=user.pk)),
        )
    else:
        qs = qs.annotate(
            is_liked=Value(False, output_field=BooleanField()),
            is_bookmarked=Value(False, output_field=BooleanField()),
        )
    return qs


def feed_qs(*, user=None, search=None):
    qs = _base_tweet_qs(user)
    if search:
        qs = qs.filter(content__icontains=search)
    return qs.order_by('-created_at', '-id')


def subscriptions_feed_qs(*, user):
    return (
        _base_tweet_qs(user)
        .filter(user__in=user.following.all())
        .order_by('-created_at', '-id')
    )


def user_tweets_qs(*, author, viewer=None):
    return _base_tweet_qs(viewer).filter(user=author).order_by('-created_at', '-id')


def bookmarks_qs(*, user):
    return (
        _base_tweet_qs(user)
        .filter(bookmarks=user)
        .order_by('-created_at', '-id')
    )


def tweet_with_comments(*, slug, user=None):
    qs = _base_tweet_qs(user).prefetch_related(
        Prefetch('comments', queryset=Comment.objects.select_related('user').order_by('-created_at'))
    )
    return get_object_or_404(qs, slug=slug)
