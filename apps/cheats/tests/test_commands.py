from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.cheats.models import (
    CheatCode,
    UserCheat,
)


class ExpireCheatsCommandTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPassword2026!",
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

        self.cheat = CheatCode.objects.create(
            name="Тестовый код",
            code="TEST",
        )

    def test_expired_activation_is_disabled(self):
        now = timezone.now()

        activation = UserCheat.objects.create(
            user=self.user,
            cheat=self.cheat,
            activated_at=(
                now - timedelta(days=10)
            ),
            expires_at=(
                now - timedelta(days=1)
            ),
            is_active=True,
        )

        output = StringIO()

        call_command(
            "expire_cheats",
            stdout=output,
        )

        activation.refresh_from_db()

        self.assertFalse(
            activation.is_active
        )

        self.assertIn(
            "Отключено истёкших активаций: 1",
            output.getvalue(),
        )