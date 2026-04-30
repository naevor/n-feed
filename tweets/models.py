import uuid

from django.conf import settings
from django.db import models
from django.db.models import Index
from django.utils.text import slugify


class Tweet(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tweets')
    content = models.TextField(max_length=280)
    media = models.FileField(upload_to='tweet_media/', blank=True, null=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_tweets', blank=True)
    retweet = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='retweets')
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    bookmarks = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='bookmarked_tweets',
        blank=True,
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            Index(fields=['-created_at']),
            Index(fields=['user', '-created_at']),
            Index(fields=['slug']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.user.username}-{self.content[:50]}") or f"tweet-{uuid.uuid4().hex[:12]}"
            slug = base_slug[:110]
            counter = 1
            while Tweet.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                suffix = f"-{counter}-{uuid.uuid4().hex[:6]}"
                slug = f"{base_slug[:120 - len(suffix)]}{suffix}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}"


class Comment(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            Index(fields=['tweet', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} commented: {self.content[:30]}"
