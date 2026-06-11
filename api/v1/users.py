from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.v1.schema import (
    FollowResponseExample,
    ForbiddenResponse,
    MePatchExample,
    NotFoundResponse,
    UnauthorizedResponse,
    UserFollowResponseSerializer,
    ValidationErrorResponse,
)
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

    @extend_schema(
        methods=["GET"],
        responses={
            200: UserPrivateSerializer,
            401: UnauthorizedResponse,
        },
    )
    @extend_schema(
        methods=["PATCH"],
        request=UserUpdateSerializer,
        responses={
            200: UserPrivateSerializer,
            400: ValidationErrorResponse,
            401: UnauthorizedResponse,
        },
        examples=[MePatchExample],
    )
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
        responses={
            200: UserFollowResponseSerializer,
            401: UnauthorizedResponse,
            404: NotFoundResponse,
        },
        examples=[FollowResponseExample],
    )
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def follow(self, request, username=None):
        target = self.get_object()
        result = services.follow_toggle(actor=request.user, target=target)
        if result is None:
            return Response({"status": "noop", "following": False})
        return Response(
            {
                "status": "following" if result else "unfollowed",
                "following": result,
            }
        )

    @extend_schema(
        responses={
            200: UserMinSerializer(many=True),
            401: UnauthorizedResponse,
            403: ForbiddenResponse,
        }
    )
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def suggestions(self, request):
        serializer = UserMinSerializer(
            suggested_users(user=request.user),
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)
