from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class AccountTests(TestCase):
    def setUp(self):
        self.password = "StrongPassword2026!"

        self.user = User.objects.create_user(
            email="user@example.com",
            password=self.password,
            display_name="Старое имя",
            registration_method="email",
            email_verified=True,
            is_active=True,
        )

    def test_anonymous_user_cannot_open_account(self):
        response = self.client.get(
            reverse("accounts:account_detail")
        )

        expected_url = (
            reverse("accounts:login")
            + "?next="
            + reverse("accounts:account_detail")
        )

        self.assertRedirects(
            response,
            expected_url,
        )

    def test_user_can_update_profile(self):
        self.client.force_login(
            self.user,
            backend=(
                "apps.accounts.backends.EmailBackend"
            ),
        )

        response = self.client.post(
            reverse("accounts:account_edit"),
            {
                "display_name": "Новое имя",
                "show_in_rating": "",
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:account_detail"),
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.display_name,
            "Новое имя",
        )

        self.assertFalse(
            self.user.show_in_rating
        )