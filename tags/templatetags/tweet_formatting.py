import re

from django import template
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

HASHTAG_RE = re.compile(r"#([\w\u0400-\u04FF]{2,50})")
MENTION_RE = re.compile(r"@([A-Za-z0-9_]{2,150})")


@register.filter
def format_tweet(value):
    text = str(escape(value or ""))

    def replace_hashtag(match):
        name = match.group(1)
        url = reverse("tags:tag_detail", args=[name.lower()])
        return f'<a href="{url}">#{name}</a>'

    def replace_mention(match):
        username = match.group(1)
        url = reverse("users:profile", args=[username])
        return f'<a href="{url}">@{username}</a>'

    text = HASHTAG_RE.sub(replace_hashtag, text)
    text = MENTION_RE.sub(replace_mention, text)
    return mark_safe(text)
