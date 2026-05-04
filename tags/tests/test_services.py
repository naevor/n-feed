from django.contrib.auth import get_user_model
from django.test import TestCase

from tags.models import Tag
from tags.services import extract_tags_from_text
from tweets.models import Tweet

User = get_user_model()


class TagServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author', password='testpass123')

    def test_extract_tags_supports_latin_cyrillic_and_deduplicates(self):
        tags = extract_tags_from_text('#Django #django #джанго #x #ok')

        self.assertEqual(tags, ['django', 'джанго', 'ok'])

    def test_tweet_save_attaches_tags(self):
        tweet = Tweet.objects.create(user=self.user, content='hello #Django #api')

        self.assertEqual(
            list(tweet.tags.order_by('name').values_list('name', flat=True)),
            ['api', 'django'],
        )

    def test_tweet_edit_replaces_stale_tags(self):
        tweet = Tweet.objects.create(user=self.user, content='hello #django')

        tweet.content = 'updated #python'
        tweet.save()

        self.assertEqual(list(tweet.tags.values_list('name', flat=True)), ['python'])
        self.assertTrue(Tag.objects.filter(name='django').exists())
