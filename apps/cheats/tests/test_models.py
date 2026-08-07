from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.cheats.models import (
    CheatCode,
    CheatReward,
    RewardType,
    UserCheat,
)


class CheatCodeModelTests(TestCase):
    def test_code_is_normalized(self):
        cheat = CheatCode.objects.create(
            name="Тестовый код",
            code="  summer2026  ",
        )

        self.assertEqual(
            cheat.code,
            "SUMMER2026",
        )

    def test_end_date_must_be_after_start_date(self):
        now = timezone.now()

        cheat = CheatCode(
            name="Неверный период",
            code="INVALID",
            valid_from=now,
            valid_until=now - timedelta(days=1),
        )

        with self.assertRaises(ValidationError):
            cheat.full_clean()

    def test_active_code_is_available(self):
        cheat = CheatCode.objects.create(
            name="Рабочий код",
            code="ACTIVE",
            valid_from=(
                timezone.now()
                - timedelta(days=1)
            ),
            valid_until=(
                timezone.now()
                + timedelta(days=1)
            ),
        )

        self.assertTrue(
            cheat.activation_is_available
        )

    def test_expired_code_is_not_available(self):
        cheat = CheatCode.objects.create(
            name="Истёкший код",
            code="EXPIRED",
            valid_from=(
                timezone.now()
                - timedelta(days=10)
            ),
            valid_until=(
                timezone.now()
                - timedelta(days=1)
            ),
        )

        self.assertFalse(
            cheat.activation_is_available
        )

    def test_expiration_is_calculated(self):
        activated_at = timezone.now()

        cheat = CheatCode.objects.create(
            name="Код на месяц",
            code="MONTH",
            duration_days=30,
        )

        expires_at = cheat.calculate_expiration(
            activated_at=activated_at,
        )

        self.assertEqual(
            expires_at,
            activated_at + timedelta(days=30),
        )


class CheatRewardModelTests(TestCase):
    def setUp(self):
        self.cheat = CheatCode.objects.create(
            name="Летний код",
            code="SUMMER",
        )

    def test_streak_reward_accepts_valid_data(self):
        reward = CheatReward(
            cheat=self.cheat,
            reward_type=(
                RewardType.STREAK_TO_STAR
            ),
            reward_data={
                "answers": 8,
            },
        )

        reward.full_clean()

    def test_streak_reward_rejects_string(self):
        reward = CheatReward(
            cheat=self.cheat,
            reward_type=(
                RewardType.STREAK_TO_STAR
            ),
            reward_data={
                "answers": "8",
            },
        )

        with self.assertRaises(ValidationError):
            reward.full_clean()

    def test_star_multiplier_requires_multiplier(self):
        reward = CheatReward(
            cheat=self.cheat,
            reward_type=(
                RewardType.DOUBLE_STARS
            ),
            reward_data={},
        )

        with self.assertRaises(ValidationError):
            reward.full_clean()

    def test_reward_data_must_be_object(self):
        reward = CheatReward(
            cheat=self.cheat,
            reward_type=RewardType.BONUS_STAR,
            reward_data=[
                1,
                2,
            ],
        )

        with self.assertRaises(ValidationError):
            reward.full_clean()


class UserCheatModelTests(TestCase):
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
            duration_days=30,
        )

    def test_activation_is_currently_active(self):
        now = timezone.now()

        activation = UserCheat.objects.create(
            user=self.user,
            cheat=self.cheat,
            activated_at=now,
            expires_at=(
                    now + timedelta(days=1)
            ),
        )

        self.assertTrue(
            activation.currently_active
        )

    def test_expired_activation_is_not_active(self):
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
        )

        self.assertFalse(
            activation.currently_active
        )