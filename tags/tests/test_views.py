from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tweets.models import Tweet

User = get_user_model()


class TagViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author', password='testpass123')

    def test_tag_page_lists_matching_tweets(self):
        Tweet.objects.create(user=self.user, content='matched #Django')
        Tweet.objects.create(user=self.user, content='other #Python')

        response = self.client.get(reverse('tags:tag_detail', args=['django']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'matched')
        self.assertNotContains(response, 'other')
