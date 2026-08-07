from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.cheats.models import (
    CheatCode,
    CheatReward,
    RewardType,
    UserCheat,
)
from apps.cheats.services.activation import (
    activate_cheat_code,
)
from apps.cheats.services.exceptions import (
    CheatCodeExpiredError,
    CheatGlobalLimitReachedError,
    CheatUserLimitReachedError,
)


class CheatActivationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPassword2026!",
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

        self.cheat = CheatCode.objects.create(
            name="Летний бонус",
            code="SUMMER2026",
            duration_days=30,
            max_user_activations=1,
        )

        CheatReward.objects.create(
            cheat=self.cheat,
            reward_type=(
                RewardType.STREAK_TO_STAR
            ),
            reward_data={
                "answers": 8,
            },
        )

    def test_code_is_activated(self):
        result = activate_cheat_code(
            user=self.user,
            raw_code=" summer2026 ",
            activation_ip="192.0.2.10",
            activation_user_agent="Test Browser",
        )

        activation = result.activation

        self.assertEqual(
            activation.user,
            self.user,
        )

        self.assertEqual(
            activation.cheat,
            self.cheat,
        )

        self.assertEqual(
            str(activation.activation_ip),
            "192.0.2.10",
        )

        self.assertTrue(
            activation.currently_active
        )

        self.cheat.refresh_from_db()

        self.assertEqual(
            self.cheat.activation_count,
            1,
        )

    def test_user_limit_is_enforced(self):
        activate_cheat_code(
            user=self.user,
            raw_code=self.cheat.code,
        )

        with self.assertRaises(
            CheatUserLimitReachedError
        ):
            activate_cheat_code(
                user=self.user,
                raw_code=self.cheat.code,
            )

        self.assertEqual(
            UserCheat.objects.filter(
                user=self.user,
                cheat=self.cheat,
            ).count(),
            1,
        )

    def test_global_limit_is_enforced(self):
        self.cheat.max_global_activations = 1
        self.cheat.save(
            update_fields=[
                "max_global_activations",
            ]
        )

        activate_cheat_code(
            user=self.user,
            raw_code=self.cheat.code,
        )

        second_user = User.objects.create_user(
            email="second@example.com",
            password="StrongPassword2026!",
            display_name="Второй",
            email_verified=True,
            is_active=True,
        )

        with self.assertRaises(
            CheatGlobalLimitReachedError
        ):
            activate_cheat_code(
                user=second_user,
                raw_code=self.cheat.code,
            )

    def test_expired_code_is_rejected(self):
        now = timezone.now()

        self.cheat.valid_from = (
            now - timedelta(days=10)
        )

        self.cheat.valid_until = (
            now - timedelta(days=1)
        )

        self.cheat.save(
            update_fields=[
                "valid_from",
                "valid_until",
            ]
        )

        with self.assertRaises(
            CheatCodeExpiredError
        ):
            activate_cheat_code(
                user=self.user,
                raw_code=self.cheat.code,
            )