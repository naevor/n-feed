from drf_spectacular.utils import OpenApiExample, OpenApiResponse, inline_serializer
from rest_framework import serializers

ErrorDetailSerializer = inline_serializer(
    name="ErrorDetail",
    fields={"detail": serializers.CharField()},
)

ValidationErrorSerializer = inline_serializer(
    name="ValidationError",
    fields={"field_name": serializers.ListField(child=serializers.CharField())},
)

UnauthorizedResponse = OpenApiResponse(
    response=ErrorDetailSerializer,
    description="Authentication credentials were missing or invalid.",
)
ForbiddenResponse = OpenApiResponse(
    response=ErrorDetailSerializer,
    description="The authenticated user does not have permission for this resource.",
)
NotFoundResponse = OpenApiResponse(
    response=ErrorDetailSerializer,
    description="The requested resource does not exist.",
)
ValidationErrorResponse = OpenApiResponse(
    response=ValidationErrorSerializer,
    description="The request payload failed validation.",
)

TweetCreateExample = OpenApiExample(
    "Create tweet",
    value={"content": "Shipping n-feed API #django"},
    request_only=True,
)
TweetCreateResponseExample = OpenApiExample(
    "Created tweet response",
    value={
        "id": 42,
        "slug": "author-shipping-n-feed-api-django",
        "user": {"id": 1, "username": "author", "avatar": None},
        "content": "Shipping n-feed API #django",
        "media": None,
        "created_at": "2026-06-12T10:00:00Z",
        "likes_count": 0,
        "comments_count": 0,
        "is_liked": False,
        "is_bookmarked": False,
    },
    response_only=True,
)

TweetActionResponseSerializer = inline_serializer(
    name="TweetActionResponse",
    fields={
        "status": serializers.CharField(),
        "liked": serializers.BooleanField(required=False),
        "bookmarked": serializers.BooleanField(required=False),
    },
)

UserFollowResponseSerializer = inline_serializer(
    name="UserFollowResponse",
    fields={
        "status": serializers.CharField(),
        "following": serializers.BooleanField(),
    },
)

NotificationMarkReadResponseSerializer = inline_serializer(
    name="NotificationMarkReadResponse",
    fields={
        "status": serializers.CharField(),
        "read": serializers.BooleanField(),
        "unread_count": serializers.IntegerField(),
    },
)

NotificationMarkAllReadResponseSerializer = inline_serializer(
    name="NotificationMarkAllReadResponse",
    fields={
        "status": serializers.CharField(),
        "marked": serializers.IntegerField(),
        "unread_count": serializers.IntegerField(),
    },
)

MePatchExample = OpenApiExample(
    "Update current user",
    value={"email": "author@example.com", "bio": "Django backend developer"},
    request_only=True,
)

FollowResponseExample = OpenApiExample(
    "Follow response",
    value={"status": "following", "following": True},
    response_only=True,
)

NotificationMarkReadExample = OpenApiExample(
    "Notification marked read",
    value={"status": "read", "read": True, "unread_count": 0},
    response_only=True,
)
