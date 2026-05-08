from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True)
    tweets = models.ManyToManyField("tweets.Tweet", related_name="tags", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"#{self.name}"
