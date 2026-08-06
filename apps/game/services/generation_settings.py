from django.db import transaction

from apps.game.models import (
    OperationGenerationSettings,
    UserGenerationSettings,
)


DEFAULT_OPERATION_SETTINGS = {
    OperationGenerationSettings.Operation.ADD: {
        "is_enabled": True,
        "mixed_mode_weight": 25,
        "first_operand_min": 1,
        "first_operand_max": 100,
        "second_operand_min": 1,
        "second_operand_max": 100,
        "operands_count": 2,
        "minimum_answer": None,
        "maximum_answer": 200,
        "allow_negative_result": False,
        "allow_remainder": False,
    },
    OperationGenerationSettings.Operation.SUB: {
        "is_enabled": True,
        "mixed_mode_weight": 25,
        "first_operand_min": 1,
        "first_operand_max": 100,
        "second_operand_min": 1,
        "second_operand_max": 100,
        "operands_count": 2,
        "minimum_answer": 0,
        "maximum_answer": 100,
        "allow_negative_result": False,
        "allow_remainder": False,
    },
    OperationGenerationSettings.Operation.MUL: {
        "is_enabled": True,
        "mixed_mode_weight": 25,
        "first_operand_min": 1,
        "first_operand_max": 10,
        "second_operand_min": 1,
        "second_operand_max": 10,
        "operands_count": 2,
        "minimum_answer": 1,
        "maximum_answer": 100,
        "allow_negative_result": False,
        "allow_remainder": False,
    },
    OperationGenerationSettings.Operation.DIV: {
        "is_enabled": True,
        "mixed_mode_weight": 25,
        "first_operand_min": 1,
        "first_operand_max": 10,
        "second_operand_min": 1,
        "second_operand_max": 10,
        "operands_count": 2,
        "minimum_answer": 1,
        "maximum_answer": 10,
        "allow_negative_result": False,
        "allow_remainder": False,
    },
}


@transaction.atomic
def create_default_generation_settings(*, user):
    """
    Создаёт общие настройки генератора и недостающие
    настройки четырёх математических действий.
    """
    generation_settings, _ = (
        UserGenerationSettings.objects.get_or_create(
            user=user,
        )
    )

    for operation, defaults in (
        DEFAULT_OPERATION_SETTINGS.items()
    ):
        (
            OperationGenerationSettings.objects
            .get_or_create(
                generation_settings=(
                    generation_settings
                ),
                operation=operation,
                defaults=defaults,
            )
        )

    return generation_settings