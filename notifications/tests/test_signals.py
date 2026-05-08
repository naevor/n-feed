from django.contrib.auth import get_user_model
from django.test import TestCase

from notifications.models import Notification
from tweets.models import Comment, Tweet

User = get_user_model()


class NotificationSignalTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username="author", password="testpass123")
        self.actor = User.objects.create_user(username="actor", password="testpass123")
        self.mentioned = User.objects.create_user(username="mentioned", password="testpass123")
        self.tweet = Tweet.objects.create(user=self.author, content="hello world")

    def test_like_creates_notification_for_tweet_author(self):
        self.tweet.likes.add(self.actor)

        notification = Notification.objects.get(kind=Notification.Kind.LIKE)
        self.assertEqual(notification.recipient, self.author)
        self.assertEqual(notification.actor, self.actor)
        self.assertEqual(notification.tweet, self.tweet)

    def test_self_like_does_not_create_notification(self):
        self.tweet.likes.add(self.author)

        self.assertFalse(Notification.objects.exists())

    def test_comment_creates_notification_for_tweet_author(self):
        Comment.objects.create(tweet=self.tweet, user=self.actor, content="nice")

        notification = Notification.objects.get(kind=Notification.Kind.COMMENT)
        self.assertEqual(notification.recipient, self.author)
        self.assertEqual(notification.actor, self.actor)
        self.assertEqual(notification.tweet, self.tweet)

    def test_follow_creates_notification_for_target_user(self):
        self.actor.following.add(self.author)

        notification = Notification.objects.get(kind=Notification.Kind.FOLLOW)
        self.assertEqual(notification.recipient, self.author)
        self.assertEqual(notification.actor, self.actor)
        self.assertIsNone(notification.tweet)

    def test_mention_creates_notification_for_mentioned_user(self):
        tweet = Tweet.objects.create(user=self.author, content="hello @mentioned")

        notification = Notification.objects.get(kind=Notification.Kind.MENTION)
        self.assertEqual(notification.recipient, self.mentioned)
        self.assertEqual(notification.actor, self.author)
        self.assertEqual(notification.tweet, tweet)

    def test_repeated_like_and_mention_do_not_duplicate_notifications(self):
        self.tweet.likes.add(self.actor)
        self.tweet.likes.remove(self.actor)
        self.tweet.likes.add(self.actor)

        tweet = Tweet.objects.create(user=self.author, content="hello @mentioned")
        tweet.save()

        self.assertEqual(Notification.objects.filter(kind=Notification.Kind.LIKE).count(), 1)
        self.assertEqual(Notification.objects.filter(kind=Notification.Kind.MENTION).count(), 1)
