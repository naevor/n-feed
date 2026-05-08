from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from tweets.models import Tweet

User = get_user_model()


class ApiV1Tests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="author", password="testpass123")
        self.other = User.objects.create_user(username="other", password="testpass123")
        self.tweet = Tweet.objects.create(user=self.user, content="hello api searchable")

    def authenticate(self, user=None):
        user = user or self.user
        self.client.force_authenticate(user=user)

    def test_jwt_login_returns_tokens(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {
                "username": "author",
                "password": "testpass123",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_schema_and_docs_are_available(self):
        schema = self.client.get("/api/schema/")
        docs = self.client.get("/api/docs/")
        redoc = self.client.get("/api/redoc/")

        self.assertEqual(schema.status_code, status.HTTP_200_OK)
        self.assertEqual(docs.status_code, status.HTTP_200_OK)
        self.assertEqual(redoc.status_code, status.HTTP_200_OK)

    def test_anonymous_can_list_and_retrieve_tweets(self):
        list_response = self.client.get("/api/v1/tweets/")
        detail_response = self.client.get(f"/api/v1/tweets/{self.tweet.slug}/")

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)

    def test_anonymous_cannot_create_tweet(self):
        response = self.client.post("/api/v1/tweets/", {"content": "blocked"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Tweet.objects.filter(content="blocked").exists())

    def test_authenticated_user_can_create_tweet(self):
        self.authenticate()

        response = self.client.post("/api/v1/tweets/", {"content": "created via api"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["content"], "created via api")
        self.assertEqual(response.data["user"]["username"], "author")

    def test_owner_can_patch_tweet(self):
        self.authenticate()

        response = self.client.patch(
            f"/api/v1/tweets/{self.tweet.slug}/",
            {"content": "patched via api"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.content, "patched via api")

    def test_non_owner_cannot_patch_or_delete_tweet(self):
        self.authenticate(self.other)

        patch_response = self.client.patch(
            f"/api/v1/tweets/{self.tweet.slug}/",
            {"content": "hacked"},
        )
        delete_response = self.client.delete(f"/api/v1/tweets/{self.tweet.slug}/")

        self.assertEqual(patch_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.content, "hello api searchable")

    def test_owner_can_delete_tweet(self):
        self.authenticate()

        response = self.client.delete(f"/api/v1/tweets/{self.tweet.slug}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tweet.objects.filter(pk=self.tweet.pk).exists())

    def test_like_and_bookmark_toggle(self):
        self.authenticate(self.other)

        like_response = self.client.post(f"/api/v1/tweets/{self.tweet.slug}/like/")
        bookmark_response = self.client.post(f"/api/v1/tweets/{self.tweet.slug}/bookmark/")

        self.assertEqual(like_response.status_code, status.HTTP_200_OK)
        self.assertEqual(bookmark_response.status_code, status.HTTP_200_OK)
        self.assertTrue(like_response.data["liked"])
        self.assertTrue(bookmark_response.data["bookmarked"])
        self.assertIn(self.other, self.tweet.likes.all())
        self.assertIn(self.other, self.tweet.bookmarks.all())

    def test_users_list_detail_and_follow(self):
        self.authenticate()

        list_response = self.client.get("/api/v1/users/")
        detail_response = self.client.get("/api/v1/users/other/")
        follow_response = self.client.post("/api/v1/users/other/follow/")

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(follow_response.status_code, status.HTTP_200_OK)
        self.assertTrue(follow_response.data["following"])
        self.assertIn(self.other, self.user.following.all())

    def test_user_suggestions_endpoint_returns_friends_of_friends(self):
        third = User.objects.create_user(username="third", password="testpass123")
        self.user.following.add(self.other)
        self.other.following.add(third)
        self.authenticate()

        response = self.client.get("/api/v1/users/suggestions/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["username"], "third")

    def test_tweet_search_filter_and_ordering(self):
        Tweet.objects.create(user=self.other, content="another api tweet")

        search_response = self.client.get("/api/v1/tweets/?search=searchable")
        filter_response = self.client.get("/api/v1/tweets/?user__username=other")
        ordering_response = self.client.get("/api/v1/tweets/?ordering=created_at")

        self.assertEqual(search_response.status_code, status.HTTP_200_OK)
        self.assertEqual(filter_response.status_code, status.HTTP_200_OK)
        self.assertEqual(ordering_response.status_code, status.HTTP_200_OK)
        self.assertEqual(search_response.data["count"], 1)
        self.assertEqual(filter_response.data["count"], 1)

    def test_tweet_tag_filter_and_trending_endpoint(self):
        cache.clear()
        Tweet.objects.create(user=self.user, content="first #Django")
        Tweet.objects.create(user=self.other, content="second #django")
        Tweet.objects.create(user=self.other, content="other #python")

        filter_response = self.client.get("/api/v1/tweets/?tags__name=django")
        trending_response = self.client.get("/api/v1/tags/trending/")

        self.assertEqual(filter_response.status_code, status.HTTP_200_OK)
        self.assertEqual(trending_response.status_code, status.HTTP_200_OK)
        self.assertEqual(filter_response.data["count"], 2)
        self.assertEqual(trending_response.data[0]["name"], "django")
        self.assertEqual(trending_response.data[0]["tweet_count"], 2)
