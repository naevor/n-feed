from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from notifications.models import Notification
from notifications.selectors import user_notifications_qs
from notifications.serializers import NotificationSerializer
from notifications.services import mark_all_read, mark_notification_read


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.none()

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset
        return user_notifications_qs(user=self.request.user)

    @extend_schema(
        responses=inline_serializer(
            name='NotificationMarkReadResponse',
            fields={'read': serializers.BooleanField()},
        )
    )
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        mark_notification_read(notification=notification)
        return Response({'read': True})

    @extend_schema(
        responses=inline_serializer(
            name='NotificationMarkAllReadResponse',
            fields={'marked': serializers.IntegerField()},
        )
    )
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        count = mark_all_read(user=request.user)
        return Response({'marked': count})
