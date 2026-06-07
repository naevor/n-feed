from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users import services
from users.selectors import suggested_users
from users.serializers import (
    UserDetailSerializer,
    UserMinSerializer,
    UserPrivateSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserDetailSerializer
    lookup_field = "username"
    search_fields = ["username"]
    ordering_fields = ["username"]
    ordering = ["username"]

    def get_queryset(self):
        return User.objects.prefetch_related("followers", "following").all()

    @extend_schema(methods=["GET"], responses=UserPrivateSerializer)
    @extend_schema(methods=["PATCH"], request=UserUpdateSerializer, responses=UserPrivateSerializer)
    @action(detail=False, methods=["get", "patch"], permission_classes=[IsAuthenticated])
    def me(self, request):
        if request.method == "PATCH":
            serializer = UserUpdateSerializer(
                request.user,
                data=request.data,
                partial=True,
                context=self.get_serializer_context(),
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

        user = User.objects.prefetch_related("followers", "following").get(pk=request.user.pk)
        return Response(UserPrivateSerializer(user, context=self.get_serializer_context()).data)

    @extend_schema(
        responses=inline_serializer(
            name="UserFollowResponse",
            fields={"following": serializers.BooleanField()},
        )
    )
    @action(detail=True, methods=["post"])
    def follow(self, request, username=None):
        target = self.get_object()
        result = services.follow_toggle(actor=request.user, target=target)
        return Response({"following": result is True})

    @extend_schema(responses=UserMinSerializer(many=True))
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def suggestions(self, request):
        serializer = UserMinSerializer(
            suggested_users(user=request.user),
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)
