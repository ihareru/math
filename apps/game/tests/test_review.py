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
from apps.game.services.review import (
    NoReviewQuestionsError,
    count_unresolved_wrong_questions,
    get_or_create_review_question,
    get_unresolved_wrong_questions,
    start_review_session,
)


class ReviewModeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPassword2026!",
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

    def create_wrong_question(self):
        game_session = start_game_session(
            user=self.user,
            mode=GameSession.Mode.MUL,
        )

        question = get_or_create_current_question(
            user=self.user,
        )

        submit_answer(
            user=self.user,
            question_id=question.pk,
            user_answer=question.correct_answer + 1,
        )

        question.refresh_from_db()

        return question

    def test_wrong_question_is_unresolved(self):
        question = self.create_wrong_question()

        unresolved = get_unresolved_wrong_questions(
            user=self.user,
        )

        self.assertIn(
            question,
            unresolved,
        )

        self.assertEqual(
            count_unresolved_wrong_questions(
                user=self.user,
            ),
            1,
        )

    def test_review_session_copies_wrong_question(self):
        source_question = self.create_wrong_question()

        review_session = start_review_session(
            user=self.user,
        )

        review_question = (
            get_or_create_review_question(
                user=self.user,
            )
        )

        self.assertEqual(
            review_question.session,
            review_session,
        )

        self.assertTrue(
            review_question.is_review
        )

        self.assertEqual(
            review_question.source_question,
            source_question,
        )

        self.assertEqual(
            review_question.operation,
            source_question.operation,
        )

        self.assertEqual(
            review_question.num1,
            source_question.num1,
        )

        self.assertEqual(
            review_question.num2,
            source_question.num2,
        )

        self.assertEqual(
            review_question.correct_answer,
            source_question.correct_answer,
        )

    def test_correct_review_resolves_error(self):
        self.create_wrong_question()

        start_review_session(
            user=self.user,
        )

        review_question = (
            get_or_create_review_question(
                user=self.user,
            )
        )

        submit_answer(
            user=self.user,
            question_id=review_question.pk,
            user_answer=(
                review_question.correct_answer
            ),
        )

        self.assertEqual(
            count_unresolved_wrong_questions(
                user=self.user,
            ),
            0,
        )

    def test_wrong_review_does_not_resolve_error(self):
        self.create_wrong_question()

        start_review_session(
            user=self.user,
        )

        review_question = (
            get_or_create_review_question(
                user=self.user,
            )
        )

        submit_answer(
            user=self.user,
            question_id=review_question.pk,
            user_answer=(
                review_question.correct_answer + 1
            ),
        )

        self.assertEqual(
            count_unresolved_wrong_questions(
                user=self.user,
            ),
            1,
        )

    def test_review_cannot_start_without_errors(self):
        with self.assertRaises(
            NoReviewQuestionsError
        ):
            start_review_session(
                user=self.user,
            )

    def test_same_error_is_not_repeated_twice_in_session(
        self,
    ):
        self.create_wrong_question()

        start_review_session(
            user=self.user,
        )

        first_review = (
            get_or_create_review_question(
                user=self.user,
            )
        )

        submit_answer(
            user=self.user,
            question_id=first_review.pk,
            user_answer=(
                first_review.correct_answer + 1
            ),
        )

        with self.assertRaises(
            NoReviewQuestionsError
        ):
            get_or_create_review_question(
                user=self.user,
            )

    def test_review_moves_to_next_unresolved_error(self):
        first_source = self.create_wrong_question()
        second_source = self.create_wrong_question()

        start_review_session(
            user=self.user,
        )

        first_review = (
            get_or_create_review_question(
                user=self.user,
            )
        )

        submit_answer(
            user=self.user,
            question_id=first_review.pk,
            user_answer=first_review.correct_answer,
        )

        second_review = (
            get_or_create_review_question(
                user=self.user,
            )
        )

        self.assertNotEqual(
            first_review.source_question_id,
            second_review.source_question_id,
        )

        source_ids = {
            first_source.pk,
            second_source.pk,
        }

        self.assertIn(
            first_review.source_question_id,
            source_ids,
        )

        self.assertIn(
            second_review.source_question_id,
            source_ids,
        )