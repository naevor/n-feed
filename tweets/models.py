import uuid

from django.db import models
from django.conf import settings
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
        blank=True
    )

    def is_bookmarked_by(self, user):
        return self.bookmarks.filter(id=user.id).exists()

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

    @property
    def total_likes(self):
        return self.likes.count()

class Comment(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='comments') 
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.username} commented: {self.content[:30]}"
