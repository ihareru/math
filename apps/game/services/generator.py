import random
from dataclasses import dataclass
from typing import Iterable

from apps.game.models import (
    GameQuestion,
    GameSession,
    OperationGenerationSettings,
    UserGenerationSettings,
)

from .generator_exceptions import (
    InvalidGenerationSettingsError,
    NoEnabledOperationsError,
    OperationDisabledError,
    QuestionGenerationError,
)


MAX_GENERATION_ATTEMPTS = 500


@dataclass(frozen=True)
class GeneratedQuestion:
    operation: str
    operands: tuple[int, ...]
    correct_answer: int

    @property
    def num1(self) -> int:
        return self.operands[0]

    @property
    def num2(self) -> int:
        return self.operands[1]

    @property
    def identity_key(self) -> tuple:
        """
        Ключ примера для исключения повторов.

        Для сложения и умножения порядок операндов
        не имеет значения.
        """
        operands = self.operands

        if self.operation in {
            GameQuestion.Operation.ADD,
            GameQuestion.Operation.MUL,
        }:
            operands = tuple(
                sorted(operands)
            )

        return (
            self.operation,
            *operands,
        )


def generate_question(
    *,
    game_session: GameSession,
    recent_identity_keys: set[
        tuple[str, int, int]
    ] | None = None,
) -> GeneratedQuestion:
    """
    Генерирует пример по персональным настройкам
    пользователя и режиму игровой сессии.

    recent_identity_keys используется для исключения
    недавно показанных примеров.
    """
    generation_settings = (
        _get_generation_settings(
            user=game_session.user,
        )
    )

    operation_settings = (
        _select_operation_settings(
            game_session=game_session,
            generation_settings=(
                generation_settings
            ),
        )
    )

    recent_identity_keys = (
        recent_identity_keys
        or set()
    )

    difficulty_level = (
        generation_settings
        .current_difficulty_level
    )

    last_valid_question = None

    for _ in range(MAX_GENERATION_ATTEMPTS):
        question = _generate_for_operation(
            operation_settings=(
                operation_settings
            ),
            difficulty_level=(
                difficulty_level
            ),
        )

        last_valid_question = question

        if (
            generation_settings
            .avoid_recent_duplicates
            and question.identity_key
            in recent_identity_keys
        ):
            continue

        return question

    if last_valid_question is not None:
        # Если диапазон слишком мал и все возможные
        # комбинации уже находятся в журнале,
        # возвращаем корректный повтор вместо ошибки 500.
        return last_valid_question

    raise QuestionGenerationError(
        "Не удалось сформировать математический пример."
    )


def build_identity_key(
    *,
    operation: str,
    num1: int | None = None,
    num2: int | None = None,
    operands=None,
) -> tuple:
    """
    Создаёт нормализованный ключ примера.
    """
    if (
        isinstance(operands, list)
        and len(operands) >= 2
    ):
        normalized_operands = tuple(
            operands
        )
    else:
        normalized_operands = (
            num1,
            num2,
        )

    if operation in {
        GameQuestion.Operation.ADD,
        GameQuestion.Operation.MUL,
    }:
        normalized_operands = tuple(
            sorted(normalized_operands)
        )

    return (
        operation,
        *normalized_operands,
    )


def _get_generation_settings(
    *,
    user,
) -> UserGenerationSettings:
    """
    Сигнал должен создавать настройки заранее.
    Дополнительный get_or_create защищает старые
    или импортированные аккаунты.
    """
    from .generation_settings import (
        create_default_generation_settings,
    )

    return create_default_generation_settings(
        user=user,
    )


def _select_operation_settings(
    *,
    game_session: GameSession,
    generation_settings: UserGenerationSettings,
) -> OperationGenerationSettings:
    """
    Возвращает настройки выбранного действия.

    Для режима ALL действие выбирается с учётом веса.
    """
    if game_session.mode == GameSession.Mode.ALL:
        return _select_weighted_operation(
            generation_settings=(
                generation_settings
            )
        )

    operation_map = {
        GameSession.Mode.ADD: (
            OperationGenerationSettings
            .Operation
            .ADD
        ),
        GameSession.Mode.SUB: (
            OperationGenerationSettings
            .Operation
            .SUB
        ),
        GameSession.Mode.MUL: (
            OperationGenerationSettings
            .Operation
            .MUL
        ),
        GameSession.Mode.DIV: (
            OperationGenerationSettings
            .Operation
            .DIV
        ),
    }

    operation = operation_map.get(
        game_session.mode
    )

    if operation is None:
        raise InvalidGenerationSettingsError(
            "Игровой режим не поддерживается генератором."
        )

    settings_object = (
        generation_settings
        .operations
        .filter(operation=operation)
        .first()
    )

    if settings_object is None:
        raise InvalidGenerationSettingsError(
            "Для выбранного действия отсутствуют настройки."
        )

    if not settings_object.is_enabled:
        raise OperationDisabledError(
            "Выбранное математическое действие отключено "
            "в настройках генератора."
        )

    return settings_object


def _select_weighted_operation(
    *,
    generation_settings: UserGenerationSettings,
) -> OperationGenerationSettings:
    operations = list(
        generation_settings
        .operations
        .filter(
            is_enabled=True,
            mixed_mode_weight__gt=0,
        )
        .order_by("operation")
    )

    if not operations:
        raise NoEnabledOperationsError(
            "В режиме «Все действия» не включено "
            "ни одного математического действия."
        )

    weights = [
        operation.mixed_mode_weight
        for operation in operations
    ]

    return random.choices(
        population=operations,
        weights=weights,
        k=1,
    )[0]


def _generate_for_operation(
    *,
    operation_settings:
        OperationGenerationSettings,
    difficulty_level: int,
) -> GeneratedQuestion:
    generators = {
        (
            OperationGenerationSettings
            .Operation
            .ADD
        ): _generate_addition,
        (
            OperationGenerationSettings
            .Operation
            .SUB
        ): _generate_subtraction,
        (
            OperationGenerationSettings
            .Operation
            .MUL
        ): _generate_multiplication,
        (
            OperationGenerationSettings
            .Operation
            .DIV
        ): _generate_division,
    }

    generator = generators.get(
        operation_settings.operation
    )

    if generator is None:
        raise InvalidGenerationSettingsError(
            "Неизвестное математическое действие."
        )

    return generator(
        settings_object=operation_settings,
        difficulty_level=difficulty_level,
    )


def _generate_addition(
    *,
    settings_object,
    difficulty_level,
) -> GeneratedQuestion:
    first_min, first_max = _scaled_range(
        minimum=settings_object.first_operand_min,
        maximum=settings_object.first_operand_max,
        difficulty_level=difficulty_level,
    )

    second_min, second_max = _scaled_range(
        minimum=settings_object.second_operand_min,
        maximum=settings_object.second_operand_max,
        difficulty_level=difficulty_level,
    )

    operands_count = min(
        max(settings_object.operands_count, 2),
        4,
    )

    for _ in range(MAX_GENERATION_ATTEMPTS):
        operands = [
            random.randint(
                first_min,
                first_max,
            )
        ]

        for _ in range(operands_count - 1):
            operands.append(
                random.randint(
                    second_min,
                    second_max,
                )
            )

        answer = calculate_answer(
            operation=GameQuestion.Operation.ADD,
            operands=operands,
        )

        if _answer_is_allowed(
            answer=answer,
            settings_object=settings_object,
        ):
            return GeneratedQuestion(
                operation=GameQuestion.Operation.ADD,
                operands=tuple(operands),
                correct_answer=answer,
            )

    raise InvalidGenerationSettingsError(
        "Диапазоны сложения не позволяют получить "
        "результат в заданных пределах."
    )


def _generate_subtraction(
    *,
    settings_object,
    difficulty_level,
) -> GeneratedQuestion:
    first_min, first_max = _scaled_range(
        minimum=settings_object.first_operand_min,
        maximum=settings_object.first_operand_max,
        difficulty_level=difficulty_level,
    )

    second_min, second_max = _scaled_range(
        minimum=settings_object.second_operand_min,
        maximum=settings_object.second_operand_max,
        difficulty_level=difficulty_level,
    )

    operands_count = min(
        max(settings_object.operands_count, 2),
        4,
    )

    for _ in range(MAX_GENERATION_ATTEMPTS):
        operands = [
            random.randint(
                first_min,
                first_max,
            )
        ]

        for _ in range(operands_count - 1):
            operands.append(
                random.randint(
                    second_min,
                    second_max,
                )
            )

        if not settings_object.allow_negative_result:
            remaining_sum = sum(
                operands[1:]
            )

            if operands[0] < remaining_sum:
                continue

        answer = calculate_answer(
            operation=GameQuestion.Operation.SUB,
            operands=operands,
        )

        if _answer_is_allowed(
            answer=answer,
            settings_object=settings_object,
        ):
            return GeneratedQuestion(
                operation=GameQuestion.Operation.SUB,
                operands=tuple(operands),
                correct_answer=answer,
            )

    raise InvalidGenerationSettingsError(
        "Диапазоны вычитания не позволяют получить "
        "результат в заданных пределах."
    )


def _generate_multiplication(
    *,
    settings_object,
    difficulty_level,
) -> GeneratedQuestion:
    first_min, first_max = _scaled_range(
        minimum=settings_object.first_operand_min,
        maximum=settings_object.first_operand_max,
        difficulty_level=difficulty_level,
    )

    second_min, second_max = _scaled_range(
        minimum=settings_object.second_operand_min,
        maximum=settings_object.second_operand_max,
        difficulty_level=difficulty_level,
    )

    operands_count = min(
        max(settings_object.operands_count, 2),
        4,
    )

    for _ in range(MAX_GENERATION_ATTEMPTS):
        operands = [
            random.randint(
                first_min,
                first_max,
            )
        ]

        for _ in range(operands_count - 1):
            operands.append(
                random.randint(
                    second_min,
                    second_max,
                )
            )

        answer = calculate_answer(
            operation=GameQuestion.Operation.MUL,
            operands=operands,
        )

        if _answer_is_allowed(
            answer=answer,
            settings_object=settings_object,
        ):
            return GeneratedQuestion(
                operation=GameQuestion.Operation.MUL,
                operands=tuple(operands),
                correct_answer=answer,
            )

    raise InvalidGenerationSettingsError(
        "Диапазоны умножения не позволяют получить "
        "результат в заданных пределах."
    )


def _generate_division(
    *,
    settings_object,
    difficulty_level,
) -> GeneratedQuestion:
    """
    В текущей версии поддерживается только
    целочисленное деление без остатка.

    first_operand_* задаёт диапазон результата.
    second_operand_* задаёт диапазон делителя.
    Делимое вычисляется как результат × делитель.
    """
    answer_min, answer_max = _scaled_range(
        minimum=settings_object.first_operand_min,
        maximum=settings_object.first_operand_max,
        difficulty_level=difficulty_level,
    )

    divisor_min, divisor_max = _scaled_range(
        minimum=settings_object.second_operand_min,
        maximum=settings_object.second_operand_max,
        difficulty_level=difficulty_level,
    )

    divisor_min = max(
        1,
        divisor_min,
    )

    if divisor_max < divisor_min:
        raise InvalidGenerationSettingsError(
            "Диапазон делителя не содержит "
            "положительных чисел."
        )

    for _ in range(MAX_GENERATION_ATTEMPTS):
        correct_answer = random.randint(
            answer_min,
            answer_max,
        )

        divisor = random.randint(
            divisor_min,
            divisor_max,
        )

        dividend = (
            correct_answer
            * divisor
        )

        if _answer_is_allowed(
            answer=correct_answer,
            settings_object=settings_object,
        ):
            return GeneratedQuestion(
                operation=GameQuestion.Operation.DIV,
                operands=(
                    dividend,
                    divisor,
                ),
                correct_answer=correct_answer,
            )

    raise InvalidGenerationSettingsError(
        "Диапазоны деления не позволяют получить "
        "результат в заданных пределах."
    )


def _scaled_range(
    *,
    minimum: int,
    maximum: int,
    difficulty_level: int,
) -> tuple[int, int]:
    """
    При автоматическом повышении сложности
    постепенно расширяет верхнюю границу диапазона.

    Фиксированный диапазон, например 10–10,
    никогда не расширяется. Это позволяет явно
    задавать конкретное число в настройках.
    """
    if maximum < minimum:
        raise InvalidGenerationSettingsError(
            "Максимум диапазона меньше минимума."
        )

    # Если пользователь задал конкретное число,
    # автоматическая сложность не должна его менять.
    if minimum == maximum:
        return minimum, maximum

    safe_level = max(
        1,
        int(difficulty_level),
    )

    if safe_level == 1:
        return minimum, maximum

    width = maximum - minimum

    increment_per_level = max(
        1,
        round(width * 0.1),
    )

    scaled_maximum = (
        maximum
        + increment_per_level
        * (safe_level - 1)
    )

    return minimum, scaled_maximum


def _answer_is_allowed(
    *,
    answer: int,
    settings_object:
        OperationGenerationSettings,
) -> bool:
    if (
        settings_object.minimum_answer
        is not None
        and answer
        < settings_object.minimum_answer
    ):
        return False

    if (
        settings_object.maximum_answer
        is not None
        and answer
        > settings_object.maximum_answer
    ):
        return False

    return True

def operation_is_enabled_for_mode(
    *,
    user,
    mode: str,
) -> bool:
    """
    Проверяет, доступен ли режим по настройкам
    генератора пользователя.
    """
    generation_settings = (
        _get_generation_settings(
            user=user,
        )
    )

    if mode == GameSession.Mode.ALL:
        return (
            generation_settings
            .operations
            .filter(
                is_enabled=True,
                mixed_mode_weight__gt=0,
            )
            .exists()
        )

    operation_map = {
        GameSession.Mode.ADD: (
            OperationGenerationSettings
            .Operation
            .ADD
        ),
        GameSession.Mode.SUB: (
            OperationGenerationSettings
            .Operation
            .SUB
        ),
        GameSession.Mode.MUL: (
            OperationGenerationSettings
            .Operation
            .MUL
        ),
        GameSession.Mode.DIV: (
            OperationGenerationSettings
            .Operation
            .DIV
        ),
    }

    operation = operation_map.get(mode)

    if operation is None:
        return False

    return (
        generation_settings
        .operations
        .filter(
            operation=operation,
            is_enabled=True,
        )
        .exists()
    )

def calculate_answer(
    *,
    operation: str,
    operands,
) -> int:
    """
    Вычисляет ответ для последовательности операндов.
    """
    if len(operands) < 2:
        raise InvalidGenerationSettingsError(
            "Недостаточно операндов."
        )

    if operation == GameQuestion.Operation.ADD:
        return sum(operands)

    if operation == GameQuestion.Operation.SUB:
        result = operands[0]

        for operand in operands[1:]:
            result -= operand

        return result

    if operation == GameQuestion.Operation.MUL:
        result = 1

        for operand in operands:
            result *= operand

        return result

    if operation == GameQuestion.Operation.DIV:
        result = operands[0]

        for operand in operands[1:]:
            if operand == 0:
                raise InvalidGenerationSettingsError(
                    "Деление на ноль невозможно."
                )

            if result % operand != 0:
                raise InvalidGenerationSettingsError(
                    "Деление должно выполняться "
                    "без остатка."
                )

            result //= operand

        return result

    raise InvalidGenerationSettingsError(
        "Неизвестная математическая операция."
    )