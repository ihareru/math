from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.analytics.models import LoginEvent


class LoginEventTests(TestCase):
    def setUp(self):
        self.password = "StrongPassword2026!"

        self.user = User.objects.create_user(
            email="user@example.com",
            password=self.password,
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

    def test_successful_login_creates_event(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "identifier": self.user.email,
                "password": self.password,
            },
            REMOTE_ADDR="192.0.2.10",
            HTTP_USER_AGENT=(
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "Gecko/20100101 Firefox/153.0"
            ),
        )

        self.assertRedirects(
            response,
            reverse("dashboard:home"),
        )

        event = LoginEvent.objects.get(
            user=self.user,
        )

        self.assertEqual(
            str(event.ip_address),
            "192.0.2.10",
        )

        self.assertEqual(
            event.browser_name,
            "Firefox",
        )

        self.assertEqual(
            event.browser_version,
            "153.0",
        )

        self.assertEqual(
            event.operating_system,
            "Windows 10/11",
        )

        self.assertEqual(
            event.device_type,
            "desktop",
        )