import random
from dataclasses import dataclass

from apps.game.models import GameQuestion, GameSession


@dataclass(frozen=True)
class GeneratedQuestion:
    operation: str
    num1: int
    num2: int
    correct_answer: int


MODE_OPERATIONS = {
    GameSession.Mode.ADD: [
        GameQuestion.Operation.ADD,
    ],
    GameSession.Mode.SUB: [
        GameQuestion.Operation.SUB,
    ],
    GameSession.Mode.MUL: [
        GameQuestion.Operation.MUL,
    ],
    GameSession.Mode.DIV: [
        GameQuestion.Operation.DIV,
    ],
    GameSession.Mode.ALL: [
        GameQuestion.Operation.ADD,
        GameQuestion.Operation.SUB,
        GameQuestion.Operation.MUL,
        GameQuestion.Operation.DIV,
    ],
}


def generate_question(mode: str) -> GeneratedQuestion:
    """
    Создаёт математический пример для указанного режима.

    Для деления всегда создаётся пример без остатка.
    Для вычитания результат не бывает отрицательным.
    """
    if mode not in MODE_OPERATIONS:
        raise ValueError(
            f"Режим {mode!r} не поддерживается генератором."
        )

    operation = random.choice(
        MODE_OPERATIONS[mode]
    )

    generators = {
        GameQuestion.Operation.ADD: _generate_addition,
        GameQuestion.Operation.SUB: _generate_subtraction,
        GameQuestion.Operation.MUL: _generate_multiplication,
        GameQuestion.Operation.DIV: _generate_division,
    }

    return generators[operation]()


def _generate_addition() -> GeneratedQuestion:
    num1 = random.randint(1, 100)
    num2 = random.randint(1, 100)

    return GeneratedQuestion(
        operation=GameQuestion.Operation.ADD,
        num1=num1,
        num2=num2,
        correct_answer=num1 + num2,
    )


def _generate_subtraction() -> GeneratedQuestion:
    num1 = random.randint(1, 100)
    num2 = random.randint(1, 100)

    if num2 > num1:
        num1, num2 = num2, num1

    return GeneratedQuestion(
        operation=GameQuestion.Operation.SUB,
        num1=num1,
        num2=num2,
        correct_answer=num1 - num2,
    )


def _generate_multiplication() -> GeneratedQuestion:
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)

    return GeneratedQuestion(
        operation=GameQuestion.Operation.MUL,
        num1=num1,
        num2=num2,
        correct_answer=num1 * num2,
    )


def _generate_division() -> GeneratedQuestion:
    divisor = random.randint(1, 10)
    correct_answer = random.randint(1, 10)
    dividend = divisor * correct_answer

    return GeneratedQuestion(
        operation=GameQuestion.Operation.DIV,
        num1=dividend,
        num2=divisor,
        correct_answer=correct_answer,
    )