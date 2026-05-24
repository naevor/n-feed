from django.core.cache import cache

from .selectors import suggested_users_cache_key


def follow_toggle(*, actor, target):
    if actor.pk == target.pk:
        return None
    if target in actor.following.all():
        actor.following.remove(target)
        cache.delete(suggested_users_cache_key(actor.pk))
        return False
    actor.following.add(target)
    cache.delete(suggested_users_cache_key(actor.pk))
    return True


def update_profile(*, user, form):
    return form.save()


def delete_account(*, user):
    user.delete()
