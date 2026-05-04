import re

from django.db import migrations

HASHTAG_RE = re.compile(r'#([\w\u0400-\u04FF]{2,50})')


def extract_tags(text):
    seen = set()
    tags = []
    for match in HASHTAG_RE.finditer(text or ''):
        name = match.group(1).lower()
        if name not in seen:
            seen.add(name)
            tags.append(name)
    return tags


def backfill_existing_tweet_tags(apps, schema_editor):
    Tweet = apps.get_model('tweets', 'Tweet')
    Tag = apps.get_model('tags', 'Tag')

    for tweet in Tweet.objects.all().iterator():
        tag_objects = []
        for name in extract_tags(tweet.content):
            tag, _ = Tag.objects.get_or_create(name=name)
            tag_objects.append(tag)
        if tag_objects:
            tweet.tags.set(tag_objects)


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(backfill_existing_tweet_tags, migrations.RunPython.noop),
    ]
