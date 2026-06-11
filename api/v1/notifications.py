from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.v1.schema import (
    NotFoundResponse,
    NotificationMarkAllReadResponseSerializer,
    NotificationMarkReadExample,
    NotificationMarkReadResponseSerializer,
    UnauthorizedResponse,
)
from notifications.models import Notification
from notifications.selectors import unread_count, user_notifications_qs
from notifications.serializers import NotificationSerializer
from notifications.services import mark_all_read, mark_notification_read


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset
        return user_notifications_qs(user=self.request.user)

    @extend_schema(
        responses={
            200: NotificationMarkReadResponseSerializer,
            401: UnauthorizedResponse,
            404: NotFoundResponse,
        },
        examples=[NotificationMarkReadExample],
    )
    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        mark_notification_read(notification=notification)
        return Response(
            {
                "status": "read",
                "read": True,
                "unread_count": unread_count(user=request.user),
            }
        )

    @extend_schema(
        responses={
            200: NotificationMarkAllReadResponseSerializer,
            401: UnauthorizedResponse,
        }
    )
    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        count = mark_all_read(user=request.user)
        return Response(
            {
                "status": "read",
                "marked": count,
                "unread_count": unread_count(user=request.user),
            }
        )
