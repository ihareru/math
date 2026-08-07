from django.test import TestCase

from apps.accounts.models import User
from apps.game.models import (
    GameQuestion,
    GameSession,
)
from apps.game.services.gameplay import (
    get_or_create_current_question,
    start_game_session,
    submit_answer,
)
from apps.game.services.statistics import (
    get_frequent_errors,
    get_operation_statistics,
    get_statistics_dashboard_data,
)


class StatisticsServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPassword2026!",
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

    def answer_question(
        self,
        *,
        mode,
        correct,
    ):
        start_game_session(
            user=self.user,
            mode=mode,
        )

        question = get_or_create_current_question(
            user=self.user,
        )

        if correct:
            answer = question.correct_answer
        else:
            answer = question.correct_answer + 1

        submit_answer(
            user=self.user,
            question_id=question.pk,
            user_answer=answer,
        )

        question.refresh_from_db()

        return question

    def test_operation_statistics(self):
        self.answer_question(
            mode=GameSession.Mode.ADD,
            correct=True,
        )

        self.answer_question(
            mode=GameSession.Mode.ADD,
            correct=False,
        )

        statistics = get_operation_statistics(
            user=self.user,
        )

        addition = next(
            item
            for item in statistics
            if item.operation
            == GameQuestion.Operation.ADD
        )

        self.assertEqual(
            addition.total_count,
            2,
        )

        self.assertEqual(
            addition.correct_count,
            1,
        )

        self.assertEqual(
            addition.wrong_count,
            1,
        )

        self.assertEqual(
            addition.accuracy_percent,
            50.0,
        )

    def test_frequent_errors_groups_examples(self):
        first = self.answer_question(
            mode=GameSession.Mode.MUL,
            correct=False,
        )

        GameQuestion.objects.create(
            session=first.session,
            sequence_number=2,
            operation=first.operation,
            num1=first.num1,
            num2=first.num2,
            correct_answer=first.correct_answer,
            user_answer=first.correct_answer + 2,
            is_correct=False,
            answered_at=first.answered_at,
            response_time_ms=1000,
        )

        errors = get_frequent_errors(
            user=self.user,
        )

        matching = next(
            item
            for item in errors
            if (
                item["operation"]
                == first.operation
                and item["num1"] == first.num1
                and item["num2"] == first.num2
            )
        )

        self.assertEqual(
            matching["error_count"],
            2,
        )

    def test_dashboard_data_contains_required_sections(
        self,
    ):
        data = get_statistics_dashboard_data(
            user=self.user,
        )

        self.assertIn(
            "statistics",
            data,
        )

        self.assertIn(
            "operation_statistics",
            data,
        )

        self.assertIn(
            "recent_sessions",
            data,
        )

        self.assertIn(
            "frequent_errors",
            data,
        )

        self.assertIn(
            "daily_statistics",
            data,
        )

        self.assertIn(
            "unresolved_errors_count",
            data,
        )