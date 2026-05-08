from django.urls import path

from . import views

app_name = "tweets"

urlpatterns = [
    path("", views.all_tweets, name="all_tweets"),
    path("subscriptions/", views.sub_tweets, name="sub_tweets"),
    path("bookmarks/", views.bookmarks_list, name="bookmarks_list"),
    path("<int:tweet_id>/bookmark/", views.toggle_bookmark, name="toggle_bookmark"),
    path("<int:tweet_id>/edit/", views.edit_tweet, name="edit_tweet"),
    path("<int:tweet_id>/delete/", views.delete_tweet, name="delete_tweet"),
    path("<int:tweet_id>/like/", views.like_tweet, name="like_tweet"),
    path("<int:tweet_id>/comment/", views.add_comment, name="add_comment"),
    path("<slug:slug>/", views.tweet_detail, name="tweet_detail"),
]
