from django import template

register = template.Library()


@register.filter
def is_bookmarked(tweet, user):
    return tweet.is_bookmarked_by(user)
