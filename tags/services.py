import re

from .models import Tag

HASHTAG_RE = re.compile(r"#([\w\u0400-\u04FF]{2,50})")


def extract_tags_from_text(text):
    seen = set()
    tags = []
    for match in HASHTAG_RE.finditer(text or ""):
        name = match.group(1).lower()
        if name not in seen:
            seen.add(name)
            tags.append(name)
    return tags


def attach_tags_to_tweet(tweet):
    names = extract_tags_from_text(tweet.content)
    tag_objects = [Tag.objects.get_or_create(name=name)[0] for name in names]
    tweet.tags.set(tag_objects)
