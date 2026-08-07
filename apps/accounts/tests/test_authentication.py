from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class AuthenticationTests(TestCase):
    def setUp(self):
        self.password = "StrongPassword2026!"

        self.user = User.objects.create_user(
            email="user@example.com",
            password=self.password,
            display_name="Игрок",
            registration_method="email",
            email_verified=True,
            is_active=True,
        )

    def test_user_can_login_by_email(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "identifier": "USER@example.com",
                "password": self.password,
            },
        )

        self.assertRedirects(
            response,
            reverse("dashboard:home"),
        )

        self.assertEqual(
            str(
                self.client.session[
                    "_auth_user_id"
                ]
            ),
            str(self.user.pk),
        )


    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.email_verified = False

        self.user.save(
            update_fields=[
                "is_active",
                "email_verified",
            ]
        )

        response = self.client.post(
            reverse("accounts:login"),
            {
                "identifier": self.user.email,
                "password": self.password,
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Регистрация не подтверждена.",
        )

    def test_invalid_email_or_password_is_rejected(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "identifier": "unknown@example.com",
                "password": self.password,
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Неверный email или пароль.",
        )