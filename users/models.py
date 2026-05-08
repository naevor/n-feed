from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    bio = models.TextField(
        max_length=500, blank=True, default="edit me, please", verbose_name="About myself"
    )
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True, verbose_name="Avatar")
    following = models.ManyToManyField(
        "self", symmetrical=False, related_name="followers", blank=True
    )
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.username
