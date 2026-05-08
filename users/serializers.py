from rest_framework import serializers

from .models import CustomUser


class UserMinSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "username", "avatar"]
        read_only_fields = fields


class UserDetailSerializer(serializers.ModelSerializer):
    followers_count = serializers.IntegerField(source="followers.count", read_only=True)
    following_count = serializers.IntegerField(source="following.count", read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "bio",
            "avatar",
            "followers_count",
            "following_count",
        ]
        read_only_fields = fields


UserSerializer = UserDetailSerializer
