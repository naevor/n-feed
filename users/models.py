from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from twitmain.uploads import validate_avatar_upload


class CustomUser(AbstractUser):
    bio = models.TextField(
        max_length=500, blank=True, default="edit me, please", verbose_name="About myself"
    )
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True, verbose_name="Avatar")
    following = models.ManyToManyField(
        "self", symmetrical=False, related_name="followers", blank=True
    )
    email = models.EmailField(blank=True, null=True)

    def clean(self):
        super().clean()
        if self.avatar:
            try:
                validate_avatar_upload(self.avatar)
            except ValidationError as exc:
                raise ValidationError({"avatar": exc.messages}) from exc

    def __str__(self):
        return self.username
