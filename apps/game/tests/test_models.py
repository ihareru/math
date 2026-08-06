from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.game.models import (
    GameQuestion,
    GameSession,
    StarTransaction,
)


class GameModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPassword2026!",
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

        self.session = GameSession.objects.create(
            user=self.user,
            mode=GameSession.Mode.DIV,
        )

    def test_division_expression_uses_colon(self):
        question = GameQuestion.objects.create(
            session=self.session,
            sequence_number=1,
            operation=GameQuestion.Operation.DIV,
            num1=10,
            num2=5,
            correct_answer=2,
        )

        self.assertEqual(
            question.expression,
            "10 : 5",
        )

    def test_question_can_store_wrong_answer(self):
        question = GameQuestion.objects.create(
            session=self.session,
            sequence_number=1,
            operation=GameQuestion.Operation.MUL,
            num1=8,
            num2=7,
            correct_answer=56,
            user_answer=53,
            is_correct=False,
            answered_at=timezone.now(),
            response_time_ms=3200,
        )

        self.assertFalse(question.is_correct)

        self.assertEqual(
            question.user_answer,
            53,
        )

        self.assertEqual(
            question.correct_answer,
            56,
        )

        self.assertEqual(
            question.response_time_seconds,
            3.2,
        )

    def test_session_accuracy(self):
        self.session.correct_count = 8
        self.session.wrong_count = 2

        self.assertEqual(
            self.session.accuracy_percent,
            80.0,
        )

    def test_star_transaction_cannot_be_zero(self):
        transaction = StarTransaction(
            user=self.user,
            session=self.session,
            amount=0,
            reason=StarTransaction.Reason.STREAK,
        )

        with self.assertRaises(ValidationError):
            transaction.full_clean()

    def test_question_expression_with_three_operands(
            self,
    ):
        user = User.objects.create_user(
            email="expression@example.com",
            password="StrongPassword2026!",
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

        game_session = GameSession.objects.create(
            user=user,
            mode=GameSession.Mode.ADD,
        )

        question = GameQuestion.objects.create(
            session=game_session,
            sequence_number=1,
            operation=GameQuestion.Operation.ADD,
            num1=5,
            num2=7,
            operands=[
                5,
                7,
                9,
            ],
            correct_answer=21,
        )

        self.assertEqual(
            question.expression,
            "5 + 7 + 9",
        )

        self.assertEqual(
            question.effective_operands,
            [
                5,
                7,
                9,
            ],
        )