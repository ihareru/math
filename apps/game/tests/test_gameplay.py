from django.test import TestCase

from apps.accounts.models import User
from apps.game.models import (
    GameQuestion,
    GameSession,
    StarTransaction,
)
from apps.game.services.exceptions import (
    QuestionAlreadyAnsweredError,
)
from apps.game.services.gameplay import (
    get_or_create_current_question,
    get_recent_answered_questions,
    start_game_session,
    submit_answer,
)
from apps.cheats.models import (
    CheatCode,
    CheatReward,
    RewardType,
)
from apps.cheats.services.activation import (
    activate_cheat_code,
)


class GameplayServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPassword2026!",
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

        self.session = start_game_session(
            user=self.user,
            mode=GameSession.Mode.ADD,
        )

    def test_refresh_does_not_create_second_question(self):
        first = get_or_create_current_question(
            user=self.user,
        )

        second = get_or_create_current_question(
            user=self.user,
        )

        self.assertEqual(
            first.pk,
            second.pk,
        )

        self.assertEqual(
            GameQuestion.objects.filter(
                session=self.session,
            ).count(),
            1,
        )

    def test_correct_answer_updates_statistics(self):
        question = get_or_create_current_question(
            user=self.user,
        )

        result = submit_answer(
            user=self.user,
            question_id=question.pk,
            user_answer=question.correct_answer,
        )

        self.assertTrue(result.is_correct)

        self.session.refresh_from_db()
        self.user.game_statistics.refresh_from_db()

        self.assertEqual(
            self.session.correct_count,
            1,
        )

        self.assertEqual(
            self.session.current_streak,
            1,
        )

        self.assertEqual(
            self.user.game_statistics.total_correct,
            1,
        )

    def test_wrong_answer_stores_correct_answer(self):
        question = get_or_create_current_question(
            user=self.user,
        )

        wrong_answer = (
            question.correct_answer + 1
        )

        result = submit_answer(
            user=self.user,
            question_id=question.pk,
            user_answer=wrong_answer,
        )

        self.assertFalse(result.is_correct)

        question.refresh_from_db()

        self.assertEqual(
            question.user_answer,
            wrong_answer,
        )

        self.assertNotEqual(
            question.user_answer,
            question.correct_answer,
        )

        self.session.refresh_from_db()

        self.assertEqual(
            self.session.current_streak,
            0,
        )

    def test_answer_cannot_be_submitted_twice(self):
        question = get_or_create_current_question(
            user=self.user,
        )

        submit_answer(
            user=self.user,
            question_id=question.pk,
            user_answer=question.correct_answer,
        )

        with self.assertRaises(
            QuestionAlreadyAnsweredError
        ):
            submit_answer(
                user=self.user,
                question_id=question.pk,
                user_answer=question.correct_answer,
            )

    def test_star_is_awarded_after_ten_correct_answers(
        self,
    ):
        for _ in range(10):
            question = get_or_create_current_question(
                user=self.user,
            )

            submit_answer(
                user=self.user,
                question_id=question.pk,
                user_answer=question.correct_answer,
            )

        self.session.refresh_from_db()
        self.user.game_statistics.refresh_from_db()

        self.assertEqual(
            self.session.current_streak,
            10,
        )

        self.assertEqual(
            self.session.stars_earned,
            1,
        )

        self.assertEqual(
            self.user.game_statistics.stars,
            1,
        )

        self.assertEqual(
            StarTransaction.objects.filter(
                user=self.user,
                reason=StarTransaction.Reason.STREAK,
                amount=1,
            ).count(),
            1,
        )

    def test_recent_history_is_limited_to_ten(self):
        for _ in range(12):
            question = get_or_create_current_question(
                user=self.user,
            )

            submit_answer(
                user=self.user,
                question_id=question.pk,
                user_answer=question.correct_answer,
            )

        recent = list(
            get_recent_answered_questions(
                user=self.user,
                limit=10,
            )
        )

        self.assertEqual(
            len(recent),
            10,
        )

    def test_cheat_awards_star_after_eight_answers(
            self,
    ):
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

        for _ in range(8):
            question = get_or_create_current_question(
                user=self.user,
            )

            submit_answer(
                user=self.user,
                question_id=question.pk,
                user_answer=question.correct_answer,
            )

        self.session.refresh_from_db()
        self.user.game_statistics.refresh_from_db()

        self.assertEqual(
            self.session.current_streak,
            8,
        )

        self.assertEqual(
            self.session.stars_earned,
            1,
        )

        self.assertEqual(
            self.user.game_statistics.stars,
            1,
        )

    def test_star_multiplier_awards_two_stars(
            self,
    ):
        cheat = CheatCode.objects.create(
            name="Двойные звёзды",
            code="DOUBLE",
            duration_days=30,
        )

        CheatReward.objects.create(
            cheat=cheat,
            reward_type=(
                RewardType.DOUBLE_STARS
            ),
            reward_data={
                "multiplier": 2,
            },
        )

        activate_cheat_code(
            user=self.user,
            raw_code=cheat.code,
        )

        last_result = None

        for _ in range(10):
            question = get_or_create_current_question(
                user=self.user,
            )

            last_result = submit_answer(
                user=self.user,
                question_id=question.pk,
                user_answer=question.correct_answer,
            )

        self.assertIsNotNone(last_result)

        self.assertEqual(
            last_result.awarded_stars,
            2,
        )

        self.session.refresh_from_db()
        self.user.game_statistics.refresh_from_db()

        self.assertEqual(
            self.session.stars_earned,
            2,
        )

        self.assertEqual(
            self.user.game_statistics.stars,
            2,
        )

    def test_freeze_streak_keeps_streak_after_error(
            self,
    ):
        cheat = CheatCode.objects.create(
            name="Заморозка серии",
            code="FREEZE",
            duration_days=30,
        )

        CheatReward.objects.create(
            cheat=cheat,
            reward_type=(
                RewardType.FREEZE_STREAK
            ),
            reward_data={
                "enabled": True,
            },
        )

        activate_cheat_code(
            user=self.user,
            raw_code=cheat.code,
        )

        first_question = (
            get_or_create_current_question(
                user=self.user,
            )
        )

        submit_answer(
            user=self.user,
            question_id=first_question.pk,
            user_answer=first_question.correct_answer,
        )

        second_question = (
            get_or_create_current_question(
                user=self.user,
            )
        )

        submit_answer(
            user=self.user,
            question_id=second_question.pk,
            user_answer=(
                    second_question.correct_answer + 1
            ),
        )

        self.session.refresh_from_db()

        self.assertEqual(
            self.session.current_streak,
            1,
        )
