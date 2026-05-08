from django.core.cache import cache
from django.db.models import Case, Count, IntegerField, Q, When
from django.shortcuts import get_object_or_404

from .models import CustomUser

SUGGESTED_USERS_CACHE_TTL_SECONDS = 3600
SUGGESTED_USERS_CACHE_LIMIT = 50


def get_user_by_username(*, username):
    return get_object_or_404(
        CustomUser.objects.prefetch_related("followers", "following"),
        username=username,
    )


def suggested_users(*, user, limit=5):
    if not user.is_authenticated:
        return CustomUser.objects.none()

    cache_key = f"suggested_users:{user.pk}:v1"
    suggested_ids = cache.get(cache_key)
    if suggested_ids is None:
        following_ids = list(user.following.values_list("id", flat=True))
        if following_ids:
            suggested_ids = list(
                CustomUser.objects.exclude(id__in=following_ids)
                .exclude(id=user.id)
                .annotate(
                    score=Count(
                        "followers",
                        filter=Q(followers__in=following_ids),
                        distinct=True,
                    )
                )
                .filter(score__gt=0)
                .order_by("-score", "username")
                .values_list("id", flat=True)[:SUGGESTED_USERS_CACHE_LIMIT]
            )
        else:
            suggested_ids = []
        cache.set(cache_key, suggested_ids, SUGGESTED_USERS_CACHE_TTL_SECONDS)

    selected_ids = suggested_ids[:limit]
    if not selected_ids:
        return CustomUser.objects.none()

    ordering = Case(
        *[When(pk=pk, then=position) for position, pk in enumerate(selected_ids)],
        output_field=IntegerField(),
    )
    return (
        CustomUser.objects.filter(pk__in=selected_ids)
        .annotate(suggestion_order=ordering)
        .order_by("suggestion_order")
    )
