import os

from django.conf import settings
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

ApiStatusResponseSerializer = inline_serializer(
    name="ApiStatusResponse",
    fields={
        "status": serializers.CharField(),
        "service": serializers.CharField(),
        "api_version": serializers.CharField(),
        "environment": serializers.CharField(),
        "debug": serializers.BooleanField(),
        "docs_url": serializers.CharField(),
        "schema_url": serializers.CharField(),
    },
)


class ApiStatusView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(responses={200: ApiStatusResponseSerializer})
    def get(self, request):
        return Response(
            {
                "status": "ok",
                "service": "n-feed",
                "api_version": "v1",
                "environment": os.environ.get("DJANGO_ENV", "dev"),
                "debug": settings.DEBUG,
                "docs_url": request.build_absolute_uri("/api/docs/"),
                "schema_url": request.build_absolute_uri("/api/schema/"),
            }
        )
