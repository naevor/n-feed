def follow_toggle(*, actor, target):
    if actor.pk == target.pk:
        return None
    if target in actor.following.all():
        actor.following.remove(target)
        return False
    actor.following.add(target)
    return True


def update_profile(*, user, form):
    return form.save()


def delete_account(*, user):
    user.delete()
