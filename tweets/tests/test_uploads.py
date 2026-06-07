from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from tweets.forms import TweetForm

TINY_GIF = (
    b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00\xff\xff\xff,"
    b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


class TweetUploadValidationTests(TestCase):
    def test_tweet_form_accepts_valid_image_media(self):
        media = SimpleUploadedFile("tweet.gif", TINY_GIF, content_type="image/gif")

        form = TweetForm({"content": "with image"}, {"media": media})

        self.assertTrue(form.is_valid(), form.errors)

    def test_tweet_form_rejects_non_image_media(self):
        media = SimpleUploadedFile("tweet.txt", b"not an image", content_type="text/plain")

        form = TweetForm({"content": "bad media"}, {"media": media})

        self.assertFalse(form.is_valid())
        self.assertIn("media", form.errors)

    @override_settings(MAX_TWEET_MEDIA_UPLOAD_SIZE=10)
    def test_tweet_form_rejects_oversized_media(self):
        media = SimpleUploadedFile("large.png", b"x" * 11, content_type="image/png")

        form = TweetForm({"content": "large media"}, {"media": media})

        self.assertFalse(form.is_valid())
        self.assertIn("larger than", str(form.errors["media"]))
