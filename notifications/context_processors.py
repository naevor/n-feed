from .selectors import unread_count as get_unread_count


def unread_count(request):
    return {
        'unread_notifications': get_unread_count(user=request.user),
    }
