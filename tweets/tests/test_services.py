from django.contrib.auth import get_user_model
from django.test import TestCase

from tweets.forms import CommentForm, TweetForm
from tweets.models import Comment, Tweet
from tweets.services import (
    add_comment,
    create_tweet,
    delete_tweet_by_user,
    toggle_bookmark,
    toggle_like,
    update_tweet,
)

User = get_user_model()


class TweetServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="author", password="testpass123")
        self.other = User.objects.create_user(username="other", password="testpass123")
        self.tweet = Tweet.objects.create(user=self.user, content="hello world")

    def test_create_tweet(self):
        form = TweetForm({"content": "new tweet"})
        self.assertTrue(form.is_valid())
        tweet = create_tweet(user=self.user, form=form)
        self.assertEqual(tweet.user, self.user)
        self.assertEqual(tweet.content, "new tweet")

    def test_toggle_like_adds_like(self):
        result = toggle_like(user=self.other, tweet=self.tweet)
        self.assertTrue(result)
        self.assertIn(self.other, self.tweet.likes.all())

    def test_toggle_like_removes_like(self):
        self.tweet.likes.add(self.other)
        result = toggle_like(user=self.other, tweet=self.tweet)
        self.assertFalse(result)
        self.assertNotIn(self.other, self.tweet.likes.all())

    def test_toggle_bookmark_adds_bookmark(self):
        result = toggle_bookmark(user=self.other, tweet=self.tweet)
        self.assertTrue(result)
        self.assertIn(self.other, self.tweet.bookmarks.all())

    def test_toggle_bookmark_removes_bookmark(self):
        self.tweet.bookmarks.add(self.other)
        result = toggle_bookmark(user=self.other, tweet=self.tweet)
        self.assertFalse(result)
        self.assertNotIn(self.other, self.tweet.bookmarks.all())

    def test_delete_tweet_by_owner(self):
        delete_tweet_by_user(user=self.user, tweet=self.tweet)
        self.assertFalse(Tweet.objects.filter(pk=self.tweet.pk).exists())

    def test_delete_tweet_by_non_owner_raises(self):
        with self.assertRaises(PermissionError):
            delete_tweet_by_user(user=self.other, tweet=self.tweet)
        self.assertTrue(Tweet.objects.filter(pk=self.tweet.pk).exists())

    def test_update_tweet_by_non_owner_raises(self):
        form = TweetForm({"content": "hacked"}, instance=self.tweet)
        self.assertTrue(form.is_valid())
        with self.assertRaises(PermissionError):
            update_tweet(user=self.other, tweet=self.tweet, form=form)

    def test_add_comment(self):
        form = CommentForm({"content": "nice tweet"})
        self.assertTrue(form.is_valid())
        comment = add_comment(user=self.other, tweet=self.tweet, form=form)
        self.assertEqual(comment.tweet, self.tweet)
        self.assertEqual(comment.user, self.other)
        self.assertEqual(Comment.objects.filter(tweet=self.tweet).count(), 1)
