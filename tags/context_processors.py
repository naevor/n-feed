from .selectors import trending_tags as get_trending_tags


def trending_tags(request):
    return {
        'trending_tags': get_trending_tags(limit=5),
    }
