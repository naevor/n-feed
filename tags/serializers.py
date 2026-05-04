from rest_framework import serializers


class TrendingTagSerializer(serializers.Serializer):
    name = serializers.CharField()
    tweet_count = serializers.IntegerField()
