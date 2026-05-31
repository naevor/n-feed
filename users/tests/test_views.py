from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class UserViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="alice", password="testpass123")
        self.other = User.objects.create_user(username="bob", password="testpass123")

    def test_profile_is_public(self):
        response = self.client.get(reverse("users:profile", args=["alice"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Profile of alice")

    def test_profile_view_accessible_when_logged_in(self):
        self.client.login(username="alice", password="testpass123")
        response = self.client.get(reverse("users:profile", args=["alice"]))
        self.assertEqual(response.status_code, 200)

    def test_own_profile_links_to_delete_account(self):
        self.client.login(username="alice", password="testpass123")

        response = self.client.get(reverse("users:profile", args=["alice"]))

        self.assertContains(response, reverse("users:delete_account"))
        self.assertContains(response, "Delete Account")

    def test_other_profile_does_not_link_to_delete_account(self):
        self.client.login(username="alice", password="testpass123")

        response = self.client.get(reverse("users:profile", args=["bob"]))

        self.assertNotContains(response, reverse("users:delete_account"))

    def test_sidebar_profile_link_points_to_authenticated_user(self):
        self.client.login(username="alice", password="testpass123")
        response = self.client.get(reverse("users:profile", args=["bob"]))
        self.assertContains(response, reverse("users:profile", args=["alice"]))
        self.assertContains(response, "Profile of bob")

    def test_public_profile_does_not_expose_email_to_other_users(self):
        self.user.email = "alice@example.com"
        self.user.save(update_fields=["email"])

        response = self.client.get(reverse("users:profile", args=["alice"]))

        self.assertNotContains(response, "alice@example.com")

    def test_logout_requires_post(self):
        self.client.login(username="alice", password="testpass123")

        response = self.client.get(reverse("users:logout"))

        self.assertEqual(response.status_code, 405)

    def test_logout_post_logs_user_out(self):
        self.client.login(username="alice", password="testpass123")

        response = self.client.post(reverse("users:logout"))

        self.assertRedirects(response, reverse("tweets:all_tweets"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_delete_account_requires_login(self):
        response = self.client.get(reverse("users:delete_account"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response["Location"])

    def test_delete_account_post_deletes_user_and_logs_out(self):
        self.client.login(username="alice", password="testpass123")

        response = self.client.post(reverse("users:delete_account"))

        self.assertRedirects(response, reverse("tweets:all_tweets"))
        self.assertFalse(User.objects.filter(username="alice").exists())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_follow_toggle_adds_following(self):
        self.client.login(username="alice", password="testpass123")
        self.client.post(reverse("users:follow", args=["bob"]))
        self.assertIn(self.other, self.user.following.all())

    def test_follow_toggle_redirects_back_to_next_url(self):
        self.client.login(username="alice", password="testpass123")
        next_url = reverse("tweets:all_tweets")

        response = self.client.post(reverse("users:follow", args=["bob"]), {"next": next_url})

        self.assertRedirects(response, next_url)

    def test_follow_toggle_removes_following(self):
        self.user.following.add(self.other)
        self.client.login(username="alice", password="testpass123")
        self.client.post(reverse("users:follow", args=["bob"]))
        self.assertNotIn(self.other, self.user.following.all())

    def test_follow_toggle_returns_json_for_async_request(self):
        self.client.login(username="alice", password="testpass123")

        response = self.client.post(
            reverse("users:follow", args=["bob"]),
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "actor_user_id": self.user.id,
                "actor_following_count": 1,
                "target_user_id": self.other.id,
                "target_username": "bob",
                "followers_count": 1,
                "following": True,
                "follow_label": "Unfollow",
            },
        )

    def test_other_profile_loads_async_follow_controls(self):
        self.client.login(username="alice", password="testpass123")

        response = self.client.get(reverse("users:profile", args=["bob"]))

        self.assertContains(response, "data-follow-form")
        self.assertContains(response, f'data-follow-target-id="{self.other.id}"')
        self.assertContains(response, "data-followers-count")
        self.assertContains(response, "social.js")

    def test_follow_self_is_noop(self):
        self.client.login(username="alice", password="testpass123")
        self.client.post(reverse("users:follow", args=["alice"]))
        self.assertNotIn(self.user, self.user.following.all())

    def test_sidebar_shows_who_to_follow_suggestions(self):
        carol = User.objects.create_user(username="carol", password="testpass123")
        self.user.following.add(self.other)
        self.other.following.add(carol)
        self.client.login(username="alice", password="testpass123")

        response = self.client.get(reverse("tweets:all_tweets"))

        self.assertContains(response, "Who to follow")
        self.assertContains(response, "carol")
        self.assertContains(response, reverse("users:follow", args=["carol"]))
        self.assertContains(response, "Follow")
