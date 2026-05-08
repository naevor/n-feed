from .selectors import suggested_users as get_suggested_users


def suggested_users(request):
    return {
        "suggested_users": get_suggested_users(user=request.user),
    }
