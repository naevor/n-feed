from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from api.v1.schema import (
    ForbiddenResponse,
    NotFoundResponse,
    TweetActionResponseSerializer,
    TweetCreateExample,
    TweetCreateResponseExample,
    UnauthorizedResponse,
    ValidationErrorResponse,
)
from tweets import services
from tweets.permissions import IsOwnerOrReadOnly
from tweets.selectors import feed_qs
from tweets.serializers import TweetCreateSerializer, TweetMediaStatusSerializer, TweetSerializer


class TweetViewSet(viewsets.ModelViewSet):
    lookup_field = "slug"
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ["user__username", "tags__name"]
    search_fields = ["content"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        return feed_qs(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return TweetCreateSerializer
        return TweetSerializer

    def get_permissions(self):
        if self.action in ("create", "like", "bookmark"):
            return [IsAuthenticated()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return super().get_permissions()

    def get_throttles(self):
        if self.action == "create":
            self.throttle_scope = "tweet_create"
        return super().get_throttles()

    def _serialize_tweet(self, tweet):
        tweet = feed_qs(user=self.request.user).get(pk=tweet.pk)
        return TweetSerializer(tweet, context=self.get_serializer_context())

    @extend_schema(
        request=TweetCreateSerializer,
        responses={
            201: TweetSerializer,
            400: ValidationErrorResponse,
            401: UnauthorizedResponse,
        },
        examples=[TweetCreateExample, TweetCreateResponseExample],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tweet = services.create_tweet(user=request.user, **serializer.validated_data)
        return Response(self._serialize_tweet(tweet).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=TweetCreateSerializer,
        responses={
            200: TweetSerializer,
            400: ValidationErrorResponse,
            401: UnauthorizedResponse,
            403: ForbiddenResponse,
            404: NotFoundResponse,
        },
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        tweet = self.get_object()
        serializer = self.get_serializer(tweet, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        tweet = services.update_tweet(
            user=request.user,
            tweet=tweet,
            **serializer.validated_data,
        )
        return Response(self._serialize_tweet(tweet).data)

    @extend_schema(
        request=TweetCreateSerializer,
        responses={
            200: TweetSerializer,
            400: ValidationErrorResponse,
            401: UnauthorizedResponse,
            403: ForbiddenResponse,
            404: NotFoundResponse,
        },
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @extend_schema(
        responses={
            204: None,
            401: UnauthorizedResponse,
            403: ForbiddenResponse,
            404: NotFoundResponse,
        }
    )
    def destroy(self, request, *args, **kwargs):
        tweet = self.get_object()
        services.delete_tweet_by_user(user=request.user, tweet=tweet)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        responses={
            200: TweetActionResponseSerializer,
            401: UnauthorizedResponse,
            404: NotFoundResponse,
        }
    )
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def like(self, request, slug=None):
        tweet = self.get_object()
        liked = services.toggle_like(user=request.user, tweet=tweet)
        return Response({"status": "liked" if liked else "unliked", "liked": liked})

    @extend_schema(
        responses={
            200: TweetActionResponseSerializer,
            401: UnauthorizedResponse,
            404: NotFoundResponse,
        }
    )
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def bookmark(self, request, slug=None):
        tweet = self.get_object()
        bookmarked = services.toggle_bookmark(user=request.user, tweet=tweet)
        return Response(
            {
                "status": "bookmarked" if bookmarked else "unbookmarked",
                "bookmarked": bookmarked,
            }
        )

    @extend_schema(
        responses={
            200: TweetMediaStatusSerializer,
            404: NotFoundResponse,
        }
    )
    @action(detail=True, methods=["get"], url_path="media-status")
    def media_status(self, request, slug=None):
        tweet = self.get_object()
        serializer = TweetMediaStatusSerializer(tweet, context=self.get_serializer_context())
        return Response(serializer.data)
