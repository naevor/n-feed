import factory

from tweets.models import Comment, Tweet
from users.tests.factories import UserFactory


class TweetFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    content = factory.Sequence(lambda n: f"test tweet content {n}")

    class Meta:
        model = Tweet


class CommentFactory(factory.django.DjangoModelFactory):
    tweet = factory.SubFactory(TweetFactory)
    user = factory.SubFactory(UserFactory)
    content = factory.Sequence(lambda n: f"test comment {n}")

    class Meta:
        model = Comment
