from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tweets.models import Tweet

User = get_user_model()


class TweetViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author', password='testpass123')
        self.tweet = Tweet.objects.create(user=self.user, content='hello searchable world')

    def test_search_filters_tweets(self):
        Tweet.objects.create(user=self.user, content='something else')
        response = self.client.get(reverse('tweets:all_tweets'), {'q': 'searchable'})
        self.assertContains(response, 'hello searchable world')
        self.assertNotContains(response, 'something else')

    def test_like_requires_post(self):
        self.client.login(username='author', password='testpass123')
        response = self.client.get(reverse('tweets:like_tweet', args=[self.tweet.id]))
        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.tweet.likes.count(), 0)

    def test_delete_requires_post(self):
        self.client.login(username='author', password='testpass123')
        response = self.client.get(reverse('tweets:delete_tweet', args=[self.tweet.id]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Tweet.objects.filter(id=self.tweet.id).exists())

    def test_anonymous_api_post_is_denied(self):
        response = self.client.post(
            reverse('tweets:tweet-list-create'),
            {'content': 'anonymous api post'},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Tweet.objects.filter(content='anonymous api post').exists())

    def test_feed_uses_likes_count_annotation(self):
        other = User.objects.create_user(username='liker', password='testpass123')
        self.tweet.likes.add(other)
        response = self.client.get(reverse('tweets:all_tweets'))
        self.assertContains(response, '1')

    def test_bookmark_requires_post(self):
        self.client.login(username='author', password='testpass123')
        response = self.client.get(reverse('tweets:toggle_bookmark', args=[self.tweet.id]))
        self.assertEqual(response.status_code, 405)
