from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse


class HealthcheckTests(TestCase):
    def test_healthz_returns_ok(self):
        response = self.client.get(reverse("healthz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_readyz_checks_dependencies(self):
        response = self.client.get(reverse("readyz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["checks"]["database"], "ok")
        self.assertEqual(response.json()["checks"]["cache"], "ok")
        self.assertEqual(response.json()["checks"]["channels"], "ok")

    def test_readyz_returns_503_when_dependency_fails(self):
        with patch("twitmain.views._check_channels", return_value="error"):
            response = self.client.get(reverse("readyz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "error")
        self.assertEqual(response.json()["checks"]["channels"], "error")

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_celeryz_returns_ok_for_eager_mode(self):
        response = self.client.get(reverse("celeryz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "checks": {
                    "celery": {
                        "status": "ok",
                        "mode": "eager",
                        "workers": 0,
                    },
                },
            },
        )

    @override_settings(CELERY_TASK_ALWAYS_EAGER=False)
    def test_celeryz_checks_worker_ping(self):
        with patch("twitmain.views.celery_app.control.ping", return_value=[{"worker": "pong"}]):
            response = self.client.get(reverse("celeryz"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["checks"]["celery"]["status"], "ok")
        self.assertEqual(response.json()["checks"]["celery"]["mode"], "worker")
        self.assertEqual(response.json()["checks"]["celery"]["workers"], 1)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=False)
    def test_celeryz_returns_503_when_worker_is_unavailable(self):
        with patch("twitmain.views.celery_app.control.ping", return_value=[]):
            response = self.client.get(reverse("celeryz"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "error")
        self.assertEqual(response.json()["checks"]["celery"]["status"], "error")
