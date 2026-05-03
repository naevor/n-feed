from rest_framework import serializers

from users.serializers import UserMinSerializer
from .models import Comment, Tweet


class CommentSerializer(serializers.ModelSerializer):
    user = UserMinSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'tweet', 'user', 'content', 'created_at']
        read_only_fields = ['id', 'tweet', 'user', 'created_at']


class TweetSerializer(serializers.ModelSerializer):
    user = UserMinSerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.BooleanField(read_only=True, required=False)
    is_bookmarked = serializers.BooleanField(read_only=True, required=False)

    class Meta:
        model = Tweet
        fields = [
            'id',
            'slug',
            'user',
            'content',
            'media',
            'created_at',
            'likes_count',
            'comments_count',
            'is_liked',
            'is_bookmarked',
        ]
        read_only_fields = fields


class TweetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tweet
        fields = ['content', 'media']
