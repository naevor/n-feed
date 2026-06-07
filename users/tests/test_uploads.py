from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from users.forms import EditProfileForm
from users.models import CustomUser

TINY_GIF = (
    b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00\xff\xff\xff,"
    b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


class AvatarUploadValidationTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="alice", password="testpass123")

    def test_profile_form_accepts_valid_avatar(self):
        avatar = SimpleUploadedFile("avatar.gif", TINY_GIF, content_type="image/gif")

        form = EditProfileForm(
            {"email": "alice@example.com", "bio": "hello"},
            {"avatar": avatar},
            instance=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_profile_form_rejects_non_image_avatar(self):
        avatar = SimpleUploadedFile("avatar.txt", b"not an image", content_type="text/plain")

        form = EditProfileForm(
            {"email": "alice@example.com", "bio": "hello"},
            {"avatar": avatar},
            instance=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("avatar", form.errors)

    @override_settings(MAX_AVATAR_UPLOAD_SIZE=10)
    def test_profile_form_rejects_oversized_avatar(self):
        avatar = SimpleUploadedFile("avatar.gif", TINY_GIF, content_type="image/gif")

        form = EditProfileForm(
            {"email": "alice@example.com", "bio": "hello"},
            {"avatar": avatar},
            instance=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("larger than", str(form.errors["avatar"]))
