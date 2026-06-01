from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from users.selectors import suggested_users
from users.services import follow_toggle

User = get_user_model()


class SuggestedUserTests(TestCase):
    def setUp(self):
        cache.clear()
        self.alice = User.objects.create_user(username="alice", password="testpass123")
        self.bob = User.objects.create_user(username="bob", password="testpass123")
        self.carol = User.objects.create_user(username="carol", password="testpass123")
        self.dave = User.objects.create_user(username="dave", password="testpass123")

    def test_suggested_users_returns_friends_of_friends(self):
        self.alice.following.add(self.bob)
        self.bob.following.add(self.carol)

        suggestions = list(suggested_users(user=self.alice))

        self.assertEqual(suggestions, [self.carol])

    def test_suggested_users_excludes_self_and_existing_follows(self):
        self.alice.following.add(self.bob, self.carol)
        self.bob.following.add(self.alice, self.carol, self.dave)

        suggestions = list(suggested_users(user=self.alice))

        self.assertEqual(suggestions, [self.dave])

    def test_suggested_users_falls_back_when_cache_is_unavailable(self):
        self.alice.following.add(self.bob)
        self.bob.following.add(self.carol)

        with (
            patch("users.selectors.cache.get", side_effect=Exception("cache down")),
            patch("users.selectors.cache.set", side_effect=Exception("cache down")),
        ):
            suggestions = list(suggested_users(user=self.alice))

        self.assertEqual(suggestions, [self.carol])

    def test_follow_toggle_ignores_cache_delete_failure(self):
        with patch("users.services.cache.delete", side_effect=Exception("cache down")):
            result = follow_toggle(actor=self.alice, target=self.bob)

        self.assertTrue(result)
        self.assertIn(self.bob, self.alice.following.all())
