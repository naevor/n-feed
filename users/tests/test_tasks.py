from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from users.forms import RegisterForm
from users.services import create_user
from users.tasks import send_welcome_email

User = get_user_model()


class UserTaskTests(TestCase):
    def test_send_welcome_email_returns_false_for_missing_user(self):
        self.assertFalse(send_welcome_email(user_id=999))

    def test_send_welcome_email_returns_false_without_email(self):
        user = User.objects.create_user(username="no_email", password="testpass123")

        self.assertFalse(send_welcome_email(user_id=user.id))

    def test_send_welcome_email_sends_message_when_email_exists(self):
        user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="testpass123",
        )

        with patch("users.tasks.send_mail") as send_mail:
            result = send_welcome_email(user_id=user.id)

        self.assertTrue(result)
        send_mail.assert_called_once()
        self.assertEqual(send_mail.call_args.kwargs["recipient_list"], ["alice@example.com"])

    def test_create_user_enqueues_welcome_email_after_commit(self):
        form = RegisterForm(
            data={
                "username": "new_user",
                "email": "new_user@example.com",
                "password1": "complex-pass-12345",
                "password2": "complex-pass-12345",
            }
        )
        self.assertTrue(form.is_valid())

        with patch("users.services.send_welcome_email.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                user = create_user(form=form)

        delay.assert_called_once_with(user_id=user.id)
