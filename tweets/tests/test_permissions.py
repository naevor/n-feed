from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from tweets.permissions import IsOwnerOrReadOnly
from tweets.tests.factories import TweetFactory
from users.tests.factories import UserFactory


class IsOwnerOrReadOnlyTests(TestCase):
    def setUp(self):
        self.owner = UserFactory()
        self.other = UserFactory()
        self.tweet = TweetFactory(user=self.owner)
        self.permission = IsOwnerOrReadOnly()
        self.factory = APIRequestFactory()

    def test_safe_methods_are_allowed_for_non_owner(self):
        request = self.factory.get("/api/v1/tweets/")
        force_authenticate(request, user=self.other)
        request.user = self.other

        result = self.permission.has_object_permission(request, None, self.tweet)

        self.assertTrue(result)

    def test_owner_can_mutate_object(self):
        request = self.factory.patch("/api/v1/tweets/")
        force_authenticate(request, user=self.owner)
        request.user = self.owner

        result = self.permission.has_object_permission(request, None, self.tweet)

        self.assertTrue(result)

    def test_non_owner_cannot_mutate_object(self):
        request = self.factory.patch("/api/v1/tweets/")
        force_authenticate(request, user=self.other)
        request.user = self.other

        result = self.permission.has_object_permission(request, None, self.tweet)

        self.assertFalse(result)
