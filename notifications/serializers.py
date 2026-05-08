from rest_framework import serializers

from users.serializers import UserMinSerializer

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor = UserMinSerializer(read_only=True)
    tweet_slug = serializers.CharField(source="tweet.slug", read_only=True)
    tweet_content = serializers.CharField(source="tweet.content", read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id",
            "actor",
            "kind",
            "tweet_slug",
            "tweet_content",
            "is_read",
            "created_at",
        )
        read_only_fields = fields
