import shutil
import tempfile
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase, override_settings

from tweets.models import Tweet

User = get_user_model()
TINY_GIF = (
    b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00\xff\xff\xff,"
    b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


def uploaded_gif(name):
    return SimpleUploadedFile(name, TINY_GIF, content_type="image/gif")


def media_path(name):
    return Path(settings.MEDIA_ROOT) / name


class MediaRootMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_root = tempfile.mkdtemp()
        cls._media_override = override_settings(MEDIA_ROOT=cls._media_root)
        cls._media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._media_override.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)
        super().tearDownClass()


class TweetMediaLifecycleTests(MediaRootMixin, TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="author", password="testpass123")

    def test_tweet_media_is_deleted_when_tweet_is_deleted(self):
        tweet = Tweet.objects.create(
            user=self.user,
            content="with media",
            media=uploaded_gif("tweet.gif"),
        )
        media_name = tweet.media.name
        self.assertTrue(media_path(media_name).exists())

        tweet.delete()

        self.assertFalse(media_path(media_name).exists())

    def test_replaced_tweet_media_is_deleted(self):
        tweet = Tweet.objects.create(
            user=self.user,
            content="with media",
            media=uploaded_gif("old.gif"),
        )
        old_name = tweet.media.name

        tweet.media = uploaded_gif("new.gif")
        tweet.save(update_fields=["media"])

        self.assertFalse(media_path(old_name).exists())
        self.assertTrue(media_path(tweet.media.name).exists())


class CleanupOrphanMediaCommandTests(MediaRootMixin, TestCase):
    def setUp(self):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
        self.user = User.objects.create_user(
            username="author",
            password="testpass123",
            avatar=uploaded_gif("avatar.gif"),
        )

    def write_media_file(self, name):
        path = media_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(TINY_GIF)
        return path

    def test_cleanup_orphan_media_reports_without_deleting_by_default(self):
        orphan = self.write_media_file("tweet_media/orphan.gif")
        output = StringIO()

        call_command("cleanup_orphan_media", stdout=output)

        self.assertTrue(orphan.exists())
        self.assertIn("Orphan media files: 1", output.getvalue())
        self.assertIn("Run again with --delete", output.getvalue())

    def test_cleanup_orphan_media_deletes_orphans_and_keeps_referenced_files(self):
        orphan = self.write_media_file("avatars/orphan.gif")
        referenced = media_path(self.user.avatar.name)
        output = StringIO()

        call_command("cleanup_orphan_media", "--delete", stdout=output)

        self.assertFalse(orphan.exists())
        self.assertTrue(referenced.exists())
        self.assertIn("Deleted orphan media files: 1", output.getvalue())
