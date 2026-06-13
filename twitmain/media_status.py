from django.db import models


class MediaProcessingStatus(models.TextChoices):
    NONE = "none", "No media"
    PENDING = "pending", "Pending"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"
