from django.conf import settings
from django.db import models
from django.db.models import Index


class Notification(models.Model):
    class Kind(models.TextChoices):
        LIKE = 'like', 'Like'
        FOLLOW = 'follow', 'Follow'
        COMMENT = 'comment', 'Comment'
        MENTION = 'mention', 'Mention'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications_sent',
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    tweet = models.ForeignKey(
        'tweets.Tweet',
        on_delete=models.CASCADE,
        related_name='notifications',
        blank=True,
        null=True,
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            Index(fields=['recipient', '-created_at']),
            Index(fields=['recipient', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f'{self.actor} -> {self.recipient}: {self.kind}'
