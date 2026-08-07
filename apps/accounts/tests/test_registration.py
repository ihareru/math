from django.core import mail
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import (
    User,
    VerificationCode,
)


class EmailRegistrationTests(TestCase):
    def test_user_can_register_by_email(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "display_name": "Аркадий",
                "email": "user@example.com",
                "password1": "StrongPassword2026!",
                "password2": "StrongPassword2026!",
                "show_in_rating": "on",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "accounts:verify_registration"
            ),
        )

        user = User.objects.get(
            email="user@example.com"
        )

        self.assertFalse(user.is_active)
        self.assertFalse(user.email_verified)

        self.assertEqual(
            VerificationCode.objects.filter(
                user=user,
                purpose="registration",
            ).count(),
            1,
        )

        self.assertEqual(len(mail.outbox), 1)

        self.assertIn(
            "Код подтверждения Math Game",
            mail.outbox[0].subject,
        )

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            email="user@example.com",
            password="StrongPassword2026!",
            display_name="Первый",
            registration_method="email",
        )

        response = self.client.post(
            reverse("accounts:register"),
            {
                "registration_method": "email",
                "display_name": "Второй",
                "email": "USER@example.com",
                "password1": "StrongPassword2026!",
                "password2": "StrongPassword2026!",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            (
                "Пользователь с таким email "
                "уже существует."
            ),
        )

        self.assertEqual(
            User.objects.filter(
                email__iexact="user@example.com"
            ).count(),
            1,
        )