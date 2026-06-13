from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from twitmain.uploads import validate_avatar_upload

from .models import CustomUser


class UserMinSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "username", "avatar", "avatar_thumbnail", "avatar_status"]
        read_only_fields = fields


class UserDetailSerializer(serializers.ModelSerializer):
    followers_count = serializers.IntegerField(source="followers.count", read_only=True)
    following_count = serializers.IntegerField(source="following.count", read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "bio",
            "avatar",
            "avatar_thumbnail",
            "avatar_status",
            "followers_count",
            "following_count",
        ]
        read_only_fields = fields


class UserPrivateSerializer(UserDetailSerializer):
    class Meta(UserDetailSerializer.Meta):
        fields = [
            "id",
            "username",
            "email",
            "bio",
            "avatar",
            "avatar_thumbnail",
            "avatar_status",
            "followers_count",
            "following_count",
        ]
        read_only_fields = fields


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["email", "bio", "avatar"]

    def validate_avatar(self, avatar):
        try:
            validate_avatar_upload(avatar)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return avatar


UserSerializer = UserDetailSerializer
