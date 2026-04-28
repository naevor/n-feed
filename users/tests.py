# A quick test to test a back of 'users' :3

from django.test import TestCase
from django.urls import reverse
from .models import CustomUser

class UserTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="testuser", password="testpass", email="test@example.com")

    def test_login(self):
        response = self.client.post(reverse('users:login'), {'username': 'testuser', 'password': 'testpass'})
        self.assertEqual(response.status_code, 302)  

    def test_edit_profile(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('users:edit_profile'), {'bio': 'New bio', 'email': 'new@example.com'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, 'New bio')
        self.assertEqual(self.user.email, 'new@example.com')
