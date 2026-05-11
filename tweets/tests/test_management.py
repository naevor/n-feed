from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from tags.models import Tag
from tweets.models import Comment, Tweet

User = get_user_model()


class SeedDemoCommandTests(TestCase):
    def test_seed_demo_creates_demo_graph(self):
        call_command("seed_demo", users=3, tweets=5, seed=1, reset=True)

        self.assertEqual(User.objects.filter(username__startswith="demo_user_").count(), 3)
        self.assertEqual(Tweet.objects.count(), 5)
        self.assertGreater(Tag.objects.count(), 0)
        self.assertGreaterEqual(Comment.objects.count(), 0)
