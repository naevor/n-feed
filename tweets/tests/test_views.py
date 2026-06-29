from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tweets.models import Tweet
from twitmain.media_status import MediaProcessingStatus

User = get_user_model()


class TweetViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="author", password="testpass123")
        self.tweet = Tweet.objects.create(user=self.user, content="hello searchable world")

    def test_search_filters_tweets(self):
        Tweet.objects.create(user=self.user, content="something else")
        response = self.client.get(reverse("tweets:all_tweets"), {"q": "searchable"})
        self.assertContains(response, "hello searchable world")
        self.assertNotContains(response, "something else")

    def test_tweet_detail_is_public(self):
        response = self.client.get(reverse("tweets:tweet_detail", args=[self.tweet.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "hello searchable world")

    def test_anonymous_comment_redirects_to_login(self):
        response = self.client.post(
            reverse("tweets:tweet_detail", args=[self.tweet.slug]),
            {"content": "anonymous comment"},
        )

        self.assertRedirects(
            response,
            f"/users/login/?next={reverse('tweets:tweet_detail', args=[self.tweet.slug])}",
        )

    def test_like_requires_post(self):
        self.client.login(username="author", password="testpass123")
        response = self.client.get(reverse("tweets:like_tweet", args=[self.tweet.id]))
        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.tweet.likes.count(), 0)

    def test_delete_requires_post(self):
        self.client.login(username="author", password="testpass123")
        response = self.client.get(reverse("tweets:delete_tweet", args=[self.tweet.id]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Tweet.objects.filter(id=self.tweet.id).exists())

    def test_non_owner_delete_returns_forbidden(self):
        User.objects.create_user(username="other", password="testpass123")
        self.client.login(username="other", password="testpass123")

        response = self.client.post(reverse("tweets:delete_tweet", args=[self.tweet.id]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Tweet.objects.filter(id=self.tweet.id).exists())

    def test_anonymous_api_post_is_denied(self):
        response = self.client.post("/api/v1/tweets/", {"content": "anonymous api post"})
        self.assertEqual(response.status_code, 401)
        self.assertFalse(Tweet.objects.filter(content="anonymous api post").exists())

    def test_feed_uses_likes_count_annotation(self):
        other = User.objects.create_user(username="liker", password="testpass123")
        self.tweet.likes.add(other)
        response = self.client.get(reverse("tweets:all_tweets"))
        self.assertContains(response, "1")

    def test_feed_loads_realtime_client(self):
        response = self.client.get(reverse("tweets:all_tweets"))

        self.assertContains(response, "data-feed-container")
        self.assertContains(response, "data-feed-list")
        self.assertContains(response, "feed.js")

    def test_feed_shows_media_processing_status(self):
        Tweet.objects.filter(pk=self.tweet.pk).update(
            media="tweet_media/original.gif",
            media_status=MediaProcessingStatus.PENDING,
        )

        response = self.client.get(reverse("tweets:all_tweets"))

        self.assertContains(response, "Preview is processing")

    def test_feed_shows_media_processing_failure(self):
        Tweet.objects.filter(pk=self.tweet.pk).update(
            media="tweet_media/original.gif",
            media_status=MediaProcessingStatus.FAILED,
        )

        response = self.client.get(reverse("tweets:all_tweets"))

        self.assertContains(response, "Preview generation failed")

    def test_authenticated_feed_loads_async_interactions_client(self):
        self.client.login(username="author", password="testpass123")
        response = self.client.get(reverse("tweets:all_tweets"))

        self.assertContains(response, 'data-tweet-interaction="like"')
        self.assertContains(response, 'data-tweet-interaction="bookmark"')
        self.assertContains(response, f'data-current-user-id="{self.user.id}"')
        self.assertContains(response, "interactions.js")

    def test_tweet_detail_loads_interactions_and_realtime_clients(self):
        self.client.login(username="author", password="testpass123")
        response = self.client.get(reverse("tweets:tweet_detail", args=[self.tweet.slug]))

        self.assertContains(response, 'data-tweet-id="')
        self.assertContains(response, "data-comment-list")
        self.assertContains(response, "data-comment-form")
        self.assertContains(response, "interactions.js")
        self.assertContains(response, "feed.js")

    def test_bookmark_requires_post(self):
        self.client.login(username="author", password="testpass123")
        response = self.client.get(reverse("tweets:toggle_bookmark", args=[self.tweet.id]))
        self.assertEqual(response.status_code, 405)

    def test_add_comment_requires_post(self):
        self.client.login(username="author", password="testpass123")
        response = self.client.get(reverse("tweets:add_comment", args=[self.tweet.id]))
        self.assertEqual(response.status_code, 405)

    def test_like_redirects_back_to_next_url(self):
        self.client.login(username="author", password="testpass123")
        next_url = reverse("users:profile", args=["author"])
        response = self.client.post(
            reverse("tweets:like_tweet", args=[self.tweet.id]),
            {"next": next_url},
        )
        self.assertRedirects(response, next_url)

    def test_like_returns_json_for_async_request(self):
        self.client.login(username="author", password="testpass123")

        response = self.client.post(
            reverse("tweets:like_tweet", args=[self.tweet.id]),
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "tweet_id": self.tweet.id,
                "likes_count": 1,
                "liked": True,
                "like_label": "Unlike",
            },
        )

    def test_bookmark_redirects_back_to_next_url(self):
        self.client.login(username="author", password="testpass123")
        next_url = reverse("users:profile", args=["author"])
        response = self.client.post(
            reverse("tweets:toggle_bookmark", args=[self.tweet.id]),
            {"next": next_url},
        )
        self.assertRedirects(response, next_url)

    def test_bookmark_returns_json_for_async_request(self):
        self.client.login(username="author", password="testpass123")

        response = self.client.post(
            reverse("tweets:toggle_bookmark", args=[self.tweet.id]),
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "tweet_id": self.tweet.id,
                "likes_count": 0,
                "bookmarked": True,
                "bookmark_label": "Remove Bookmark",
            },
        )

    def test_tweet_detail_returns_json_for_async_comment(self):
        self.client.login(username="author", password="testpass123")

        response = self.client.post(
            reverse("tweets:tweet_detail", args=[self.tweet.slug]),
            {"content": "async comment #tag"},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["comment"]
        self.assertEqual(payload["tweet_id"], self.tweet.id)
        self.assertEqual(payload["content"], "async comment #tag")
        self.assertIn('href="/tags/tag/"', payload["content_html"])

    def test_invalid_async_comment_returns_errors(self):
        self.client.login(username="author", password="testpass123")

        response = self.client.post(
            reverse("tweets:tweet_detail", args=[self.tweet.slug]),
            {"content": "x" * 151},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.json())

    def test_edit_tweet_redirects_back_to_next_url(self):
        self.client.login(username="author", password="testpass123")
        next_url = reverse("users:profile", args=["author"])

        response = self.client.post(
            reverse("tweets:edit_tweet", args=[self.tweet.id]),
            {"content": "edited from profile", "next": next_url},
        )

        self.assertRedirects(response, next_url)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.content, "edited from profile")

    def test_edit_tweet_cancel_uses_next_url(self):
        self.client.login(username="author", password="testpass123")
        next_url = reverse("users:profile", args=["author"])

        response = self.client.get(
            reverse("tweets:edit_tweet", args=[self.tweet.id]), {"next": next_url}
        )

        self.assertContains(response, f'value="{next_url}"')
        self.assertContains(response, f'href="{next_url}"')

    def test_subscriptions_page_renders_tweet_form(self):
        self.client.login(username="author", password="testpass123")
        response = self.client.get(reverse("tweets:sub_tweets"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
