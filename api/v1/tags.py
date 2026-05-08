from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from tags.selectors import trending_tags
from tags.serializers import TrendingTagSerializer


class TagViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="limit",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Maximum number of trending tags to return.",
            ),
        ],
        responses=TrendingTagSerializer(many=True),
    )
    @action(detail=False, methods=["get"])
    def trending(self, request):
        raw_limit = request.query_params.get("limit", 10)
        try:
            limit = max(1, min(int(raw_limit), 50))
        except (TypeError, ValueError):
            limit = 10
        serializer = TrendingTagSerializer(trending_tags(limit=limit), many=True)
        return Response(serializer.data)
