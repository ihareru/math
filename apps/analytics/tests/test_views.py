import json

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.analytics.models import VisitSession


class ClientContextViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPassword2026!",
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

        self.client.force_login(
            self.user,
            backend=(
                "apps.accounts.backends.EmailBackend"
            ),
        )

    def test_client_context_is_saved(self):
        response = self.client.post(
            reverse("analytics:client_context"),
            data=json.dumps(
                {
                    "screen_width": 1920,
                    "screen_height": 1080,
                    "viewport_width": 1536,
                    "viewport_height": 864,
                    "pixel_ratio": 1.25,
                    "language": "ru-RU",
                    "timezone": "Europe/Tallinn",
                    "touch_points": 0,
                    "cpu_cores": 8,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        visit = VisitSession.objects.get(
            user=self.user,
        )

        self.assertEqual(
            visit.screen_width,
            1920,
        )

        self.assertEqual(
            visit.screen_height,
            1080,
        )

        self.assertEqual(
            visit.timezone_name,
            "Europe/Tallinn",
        )

        self.assertEqual(
            visit.cpu_cores,
            8,
        )

    def test_anonymous_request_is_rejected(self):
        self.client.logout()

        response = self.client.post(
            reverse("analytics:client_context"),
            data="{}",
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            302,
        )