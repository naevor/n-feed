import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase, override_settings

from twitmain.media_status import MediaProcessingStatus

User = get_user_model()
TINY_GIF = (
    b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00\xff\xff\xff,"
    b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


def uploaded_gif(name):
    return SimpleUploadedFile(name, TINY_GIF, content_type="image/gif")


def media_path(name):
    return Path(settings.MEDIA_ROOT) / name


class AvatarLifecycleTests(TransactionTestCase):
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

    def test_replaced_avatar_is_deleted(self):
        user = User.objects.create_user(
            username="author",
            password="testpass123",
            avatar=uploaded_gif("old.gif"),
        )
        user.refresh_from_db()
        old_name = user.avatar.name
        old_thumbnail_name = user.avatar_thumbnail.name

        user.avatar = uploaded_gif("new.gif")
        user.save(update_fields=["avatar"])
        user.refresh_from_db()

        self.assertFalse(media_path(old_name).exists())
        self.assertFalse(media_path(old_thumbnail_name).exists())
        self.assertTrue(media_path(user.avatar.name).exists())
        self.assertTrue(media_path(user.avatar_thumbnail.name).exists())
        self.assertEqual(user.avatar_status, MediaProcessingStatus.READY)

    def test_avatar_is_deleted_when_user_is_deleted(self):
        user = User.objects.create_user(
            username="author",
            password="testpass123",
            avatar=uploaded_gif("avatar.gif"),
        )
        user.refresh_from_db()
        avatar_name = user.avatar.name
        thumbnail_name = user.avatar_thumbnail.name
        self.assertTrue(media_path(avatar_name).exists())
        self.assertTrue(media_path(thumbnail_name).exists())
        self.assertEqual(user.avatar_status, MediaProcessingStatus.READY)

        user.delete()

        self.assertFalse(media_path(avatar_name).exists())
        self.assertFalse(media_path(thumbnail_name).exists())
