from django.shortcuts import get_object_or_404

from .models import CustomUser


def get_user_by_username(*, username):
    return get_object_or_404(
        CustomUser.objects.prefetch_related('followers', 'following'),
        username=username,
    )
