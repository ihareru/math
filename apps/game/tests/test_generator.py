from django.test import SimpleTestCase

from apps.game.models import (
    GameQuestion,
    GameSession,
)
from apps.game.services.generator import (
    generate_question,
)


class QuestionGeneratorTests(SimpleTestCase):
    def test_addition_answer_is_correct(self):
        question = generate_question(
            GameSession.Mode.ADD
        )

        self.assertEqual(
            question.operation,
            GameQuestion.Operation.ADD,
        )

        self.assertEqual(
            question.correct_answer,
            question.num1 + question.num2,
        )

    def test_subtraction_is_not_negative(self):
        for _ in range(100):
            question = generate_question(
                GameSession.Mode.SUB
            )

            self.assertGreaterEqual(
                question.correct_answer,
                0,
            )

            self.assertEqual(
                question.correct_answer,
                question.num1 - question.num2,
            )

    def test_multiplication_answer_is_correct(self):
        question = generate_question(
            GameSession.Mode.MUL
        )

        self.assertEqual(
            question.correct_answer,
            question.num1 * question.num2,
        )

    def test_division_has_no_remainder(self):
        for _ in range(100):
            question = generate_question(
                GameSession.Mode.DIV
            )

            self.assertNotEqual(
                question.num2,
                0,
            )

            self.assertEqual(
                question.num1 % question.num2,
                0,
            )

            self.assertEqual(
                question.correct_answer,
                question.num1 // question.num2,
            )

    def test_all_mode_uses_supported_operation(self):
        allowed_operations = {
            GameQuestion.Operation.ADD,
            GameQuestion.Operation.SUB,
            GameQuestion.Operation.MUL,
            GameQuestion.Operation.DIV,
        }

        for _ in range(100):
            question = generate_question(
                GameSession.Mode.ALL
            )

            self.assertIn(
                question.operation,
                allowed_operations,
            )