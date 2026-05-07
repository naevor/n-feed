from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class UserViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.other = User.objects.create_user(username='bob', password='testpass123')

    def test_profile_requires_login(self):
        response = self.client.get(reverse('users:profile', args=['alice']))
        self.assertRedirects(response, f"/users/login/?next=/users/profile/alice/")

    def test_profile_view_accessible_when_logged_in(self):
        self.client.login(username='alice', password='testpass123')
        response = self.client.get(reverse('users:profile', args=['alice']))
        self.assertEqual(response.status_code, 200)

    def test_sidebar_profile_link_points_to_authenticated_user(self):
        self.client.login(username='alice', password='testpass123')
        response = self.client.get(reverse('users:profile', args=['bob']))
        self.assertContains(response, reverse('users:profile', args=['alice']))
        self.assertContains(response, 'Profile of bob')

    def test_follow_toggle_adds_following(self):
        self.client.login(username='alice', password='testpass123')
        self.client.post(reverse('users:follow', args=['bob']))
        self.assertIn(self.other, self.user.following.all())

    def test_follow_toggle_removes_following(self):
        self.user.following.add(self.other)
        self.client.login(username='alice', password='testpass123')
        self.client.post(reverse('users:follow', args=['bob']))
        self.assertNotIn(self.other, self.user.following.all())

    def test_follow_self_is_noop(self):
        self.client.login(username='alice', password='testpass123')
        self.client.post(reverse('users:follow', args=['alice']))
        self.assertNotIn(self.user, self.user.following.all())

    def test_sidebar_shows_who_to_follow_suggestions(self):
        carol = User.objects.create_user(username='carol', password='testpass123')
        self.user.following.add(self.other)
        self.other.following.add(carol)
        self.client.login(username='alice', password='testpass123')

        response = self.client.get(reverse('tweets:all_tweets'))

        self.assertContains(response, 'Who to follow')
        self.assertContains(response, 'carol')
