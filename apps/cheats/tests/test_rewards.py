from django.test import TestCase

from apps.accounts.models import User
from apps.cheats.models import (
    CheatCode,
    CheatReward,
    RewardType,
)
from apps.cheats.services.activation import (
    activate_cheat_code,
)
from apps.cheats.services.rewards import (
    get_active_game_rewards,
)


class ActiveRewardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPassword2026!",
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

    def test_default_rules_without_cheats(self):
        rewards = get_active_game_rewards(
            user=self.user,
        )

        self.assertEqual(
            rewards.streak_to_star,
            10,
        )

        self.assertEqual(
            rewards.star_multiplier,
            1,
        )

        self.assertFalse(
            rewards.freeze_streak
        )

    def test_active_code_changes_streak_threshold(self):
        cheat = CheatCode.objects.create(
            name="Восемь ответов",
            code="EIGHT",
            duration_days=30,
        )

        CheatReward.objects.create(
            cheat=cheat,
            reward_type=(
                RewardType.STREAK_TO_STAR
            ),
            reward_data={
                "answers": 8,
            },
        )

        activate_cheat_code(
            user=self.user,
            raw_code=cheat.code,
        )

        rewards = get_active_game_rewards(
            user=self.user,
        )

        self.assertEqual(
            rewards.streak_to_star,
            8,
        )