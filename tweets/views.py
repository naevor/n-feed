from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CommentForm, TweetForm
from .models import Tweet
from .selectors import bookmarks_qs, feed_qs, subscriptions_feed_qs, tweet_with_comments
from . import services

PAGE_SIZE = 20


def _redirect_after_action(request):
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect('tweets:all_tweets')


def all_tweets(request):
    query = request.GET.get('q', '')
    qs = feed_qs(user=request.user, search=query or None)
    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get('page'))

    form = TweetForm()
    if request.method == 'POST' and request.user.is_authenticated:
        form = TweetForm(request.POST, request.FILES)
        if form.is_valid():
            services.create_tweet(user=request.user, form=form)
            return redirect('tweets:all_tweets')

    return render(request, 'tweets/tweet_list.html', {
        'page': page,
        'form': form,
        'query': query,
    })


@login_required
def sub_tweets(request):
    qs = subscriptions_feed_qs(user=request.user)
    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get('page'))
    return render(request, 'tweets/tweet_list.html', {
        'page': page,
        'form': TweetForm(),
        'query': '',
    })


@login_required
@require_POST
def toggle_bookmark(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    services.toggle_bookmark(user=request.user, tweet=tweet)
    return _redirect_after_action(request)


@login_required
def bookmarks_list(request):
    qs = bookmarks_qs(user=request.user)
    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get('page'))
    return render(request, 'tweets/bookmarks_list.html', {'page': page})


@login_required
def tweet_detail(request, slug):
    tweet = tweet_with_comments(slug=slug, user=request.user)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            services.add_comment(user=request.user, tweet=tweet, form=form)
            return redirect('tweets:tweet_detail', slug=slug)
    else:
        form = CommentForm()

    return render(request, 'tweets/tweet_detail.html', {
        'tweet': tweet,
        'comments': tweet.comments.all(),
        'form': form,
    })


@login_required
def edit_tweet(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    if request.user != tweet.user:
        return redirect('tweets:all_tweets')
    if request.method == 'POST':
        form = TweetForm(request.POST, request.FILES, instance=tweet)
        if form.is_valid():
            services.update_tweet(user=request.user, tweet=tweet, form=form)
            return redirect('tweets:all_tweets')
    else:
        form = TweetForm(instance=tweet)
    return render(request, 'tweets/edit_tweet.html', {'form': form})


@login_required
@require_POST
def delete_tweet(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    try:
        services.delete_tweet_by_user(user=request.user, tweet=tweet)
    except PermissionError:
        pass
    return _redirect_after_action(request)


@login_required
@require_POST
def like_tweet(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    services.toggle_like(user=request.user, tweet=tweet)
    return _redirect_after_action(request)


@login_required
def add_comment(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            services.add_comment(user=request.user, tweet=tweet, form=form)
    return redirect('tweets:all_tweets')
