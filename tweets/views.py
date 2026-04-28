from django.contrib.auth.decorators import login_required
from django.shortcuts import render , get_object_or_404 , redirect
from django.views.decorators.http import require_POST
from .models import Tweet
from .forms import TweetForm , CommentForm
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .serializers import TweetSerializer



def all_tweets(request):
    query = request.GET.get('q', '')
    if query:
        tweets = Tweet.objects.filter(content__icontains=query).order_by('-created_at')
    else:
        tweets = Tweet.objects.all().order_by('-created_at')

    form = TweetForm()
    if request.method == 'POST' and request.user.is_authenticated:
        form = TweetForm(request.POST , request.FILES)
        if form.is_valid():
            tweet = form.save(commit=False)
            tweet.user = request.user
            tweet.save()
            return redirect('tweets:all_tweets')
    return render(request, 'tweets/tweet_list.html', {
        'tweets': tweets, 
        'form': form, 
        'query': query
    })

@login_required
def sub_tweets(request):
    tweets = Tweet.objects.filter(
        Q(user__in=request.user.following.all())
    ).order_by('-created_at')
    return render(request, 'tweets/tweet_list.html', {'tweets':tweets})

@login_required
@require_POST
def toggle_bookmark(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    if tweet.is_bookmarked_by(request.user):
        tweet.bookmarks.remove(request.user)
    else:
        tweet.bookmarks.add(request.user)
    return redirect('tweets:all_tweets')

@login_required
def bookmarks_list(request):
    bookmarks = request.user.bookmarked_tweets.all().order_by('-created_at')
    return render(request, 'tweets/bookmarks_list.html', {'bookmarks': bookmarks})

@login_required
def tweet_detail(request, slug):
    tweet = get_object_or_404(Tweet, slug=slug)
    comments = tweet.comments.all().order_by('-created_at')

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.tweet = tweet 
            comment.save()
            return redirect('tweets:tweet_detail', slug=slug)
    else:
        form = CommentForm()

    return render(
        request, 'tweets/tweet_detail.html', {
            'tweet': tweet,
            'comments': comments,
            'form':form,
        }
    )


@login_required
def edit_tweet(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    if request.user != tweet.user:
        return redirect('tweets:all_tweets')
    if request.method == 'POST':
        form = TweetForm(request.POST, request.FILES, instance=tweet)
        if form.is_valid():
            form.save()
            return redirect('tweets:all_tweets')
    else:
        form = TweetForm(instance=tweet)
    return render(request, 'tweets/edit_tweet.html' , {'form': form})

@login_required
@require_POST
def delete_tweet(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    if request.user == tweet.user:
        tweet.delete()
    return redirect('tweets:all_tweets')

@login_required
@require_POST
def like_tweet(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    if request.user in tweet.likes.all():
        tweet.likes.remove(request.user)
    else:
        tweet.likes.add(request.user)
    return redirect('tweets:all_tweets')

@login_required 
def add_comment(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.tweet = tweet 
            comment.save()
            return redirect('tweets:all_tweets')
    return redirect('tweets:all_tweets')


class TweetListCreateAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        tweets = Tweet.objects.all()
        serializer = TweetSerializer(tweets , many=True)
        return Response(serializer.data)
        
    def post(self, request):
        serializer = TweetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
