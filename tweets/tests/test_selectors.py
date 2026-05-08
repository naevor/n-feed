from django.test import TestCase

from tweets.selectors import feed_qs
from tweets.tests.factories import CommentFactory, TweetFactory
from users.tests.factories import UserFactory


class TweetSelectorTests(TestCase):
    def test_feed_qs_adds_counts_and_viewer_flags(self):
        viewer = UserFactory()
        tweet = TweetFactory()
        tweet.likes.add(viewer)
        tweet.bookmarks.add(viewer)
        CommentFactory(tweet=tweet)

        selected = feed_qs(user=viewer).get(pk=tweet.pk)

        self.assertEqual(selected.likes_count, 1)
        self.assertEqual(selected.comments_count, 1)
        self.assertTrue(selected.is_liked)
        self.assertTrue(selected.is_bookmarked)

    def test_feed_qs_keeps_user_access_to_one_query(self):
        viewer = UserFactory()
        TweetFactory.create_batch(3)

        with self.assertNumQueries(1):
            rows = list(feed_qs(user=viewer))
            usernames = [tweet.user.username for tweet in rows]
            likes = [tweet.likes_count for tweet in rows]

        self.assertEqual(len(usernames), 3)
        self.assertEqual(likes, [0, 0, 0])
