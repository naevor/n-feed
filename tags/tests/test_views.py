from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from tags.selectors import trending_tags
from tweets.models import Tweet

User = get_user_model()


class TagViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="author", password="testpass123")

    def test_tag_page_lists_matching_tweets(self):
        Tweet.objects.create(user=self.user, content="matched #Django")
        Tweet.objects.create(user=self.user, content="other #Python")

        response = self.client.get(reverse("tags:tag_detail", args=["django"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "matched")
        self.assertNotContains(response, "other")

    def test_sidebar_shows_trending_tags(self):
        Tweet.objects.create(user=self.user, content="matched #Django")

        response = self.client.get(reverse("tweets:all_tweets"))

        self.assertContains(response, "Trends")
        self.assertContains(response, "#django")

    def test_trending_tags_falls_back_when_cache_is_unavailable(self):
        Tweet.objects.create(user=self.user, content="matched #Django")

        with (
            patch("tags.selectors.cache.get", side_effect=Exception("cache down")),
            patch("tags.selectors.cache.set", side_effect=Exception("cache down")),
        ):
            result = trending_tags()

        self.assertEqual(result, [{"name": "django", "tweet_count": 1}])
