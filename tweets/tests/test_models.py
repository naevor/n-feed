from django.contrib.auth import get_user_model
from django.test import TestCase

from tweets.models import Tweet

User = get_user_model()


class TweetSlugTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author', password='testpass123')

    def test_cyrillic_content_gets_non_empty_unique_slug(self):
        tweet = Tweet.objects.create(user=self.user, content='привет мир')
        self.assertTrue(tweet.slug)

    def test_slug_is_unique_for_identical_content(self):
        t1 = Tweet.objects.create(user=self.user, content='same content')
        t2 = Tweet.objects.create(user=self.user, content='same content')
        self.assertNotEqual(t1.slug, t2.slug)

    def test_emoji_content_gets_non_empty_slug(self):
        tweet = Tweet.objects.create(user=self.user, content='🔥🔥🔥')
        self.assertTrue(tweet.slug)
