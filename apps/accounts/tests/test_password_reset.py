import re

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class PasswordResetTests(TestCase):
    def setUp(self):
        self.old_password = "OldStrongPassword2026!"
        self.new_password = "NewStrongPassword2026!"

        self.user = User.objects.create_user(
            email="user@example.com",
            password=self.old_password,
            display_name="Игрок",
            registration_method="email",
            email_verified=True,
            is_active=True,
        )

    def request_reset_code(self):
        return self.client.post(
            reverse(
                "accounts:password_reset_request"
            ),
            {
                "email": self.user.email,
            },
        )

    def extract_code(self):
        email_body = mail.outbox[-1].body

        match = re.search(
            r"\b(\d{6})\b",
            email_body,
        )

        self.assertIsNotNone(match)

        return match.group(1)

    def test_reset_code_is_sent(self):
        response = self.request_reset_code()

        self.assertRedirects(
            response,
            reverse(
                "accounts:password_reset_verify"
            ),
        )

        self.assertEqual(len(mail.outbox), 1)

        self.assertIn(
            "Восстановление пароля",
            mail.outbox[0].subject,
        )

    def test_user_can_reset_password(self):
        self.request_reset_code()

        code = self.extract_code()

        response = self.client.post(
            reverse(
                "accounts:password_reset_verify"
            ),
            {
                "code": code,
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "accounts:password_reset_confirm"
            ),
        )

        response = self.client.post(
            reverse(
                "accounts:password_reset_confirm"
            ),
            {
                "password1": self.new_password,
                "password2": self.new_password,
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:login"),
        )

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password(
                self.new_password
            )
        )

    def test_wrong_code_is_rejected(self):
        self.request_reset_code()

        response = self.client.post(
            reverse(
                "accounts:password_reset_verify"
            ),
            {
                "code": "000000",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Введён неверный код.",
        )
        