from django.test import SimpleTestCase

from tags.templatetags.tweet_formatting import format_tweet


class TweetFormattingTests(SimpleTestCase):
    def test_format_tweet_links_hashtags_and_mentions(self):
        rendered = str(format_tweet("hello #Django @author"))

        self.assertIn('<a href="/tags/django/">#Django</a>', rendered)
        self.assertIn('<a href="/users/profile/author/">@author</a>', rendered)

    def test_format_tweet_escapes_html_before_linking(self):
        rendered = str(format_tweet("<script>alert(1)</script> #safe"))

        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", rendered)
        self.assertNotIn("<script>", rendered)
        self.assertIn('<a href="/tags/safe/">#safe</a>', rendered)
