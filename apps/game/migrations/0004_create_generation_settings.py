from django.conf import settings
from django.db import migrations


DEFAULTS = {
    "add": {
        "is_enabled": True,
        "mixed_mode_weight": 25,
        "first_operand_min": 1,
        "first_operand_max": 100,
        "second_operand_min": 1,
        "second_operand_max": 100,
        "operands_count": 2,
        "maximum_answer": 200,
    },
    "sub": {
        "is_enabled": True,
        "mixed_mode_weight": 25,
        "first_operand_min": 1,
        "first_operand_max": 100,
        "second_operand_min": 1,
        "second_operand_max": 100,
        "operands_count": 2,
        "minimum_answer": 0,
        "maximum_answer": 100,
    },
    "mul": {
        "is_enabled": True,
        "mixed_mode_weight": 25,
        "first_operand_min": 1,
        "first_operand_max": 10,
        "second_operand_min": 1,
        "second_operand_max": 10,
        "operands_count": 2,
        "minimum_answer": 1,
        "maximum_answer": 100,
    },
    "div": {
        "is_enabled": True,
        "mixed_mode_weight": 25,
        "first_operand_min": 1,
        "first_operand_max": 10,
        "second_operand_min": 1,
        "second_operand_max": 10,
        "operands_count": 2,
        "minimum_answer": 1,
        "maximum_answer": 10,
    },
}


def create_settings(apps, schema_editor):
    User = apps.get_model(
        settings.AUTH_USER_MODEL,
    )

    UserGenerationSettings = apps.get_model(
        "game",
        "UserGenerationSettings",
    )

    OperationGenerationSettings = apps.get_model(
        "game",
        "OperationGenerationSettings",
    )

    for user in User.objects.iterator():
        generation_settings, _ = (
            UserGenerationSettings.objects.get_or_create(
                user_id=user.pk,
            )
        )

        for operation, defaults in DEFAULTS.items():
            (
                OperationGenerationSettings.objects
                .get_or_create(
                    generation_settings_id=(
                        generation_settings.pk
                    ),
                    operation=operation,
                    defaults=defaults,
                )
            )


def reverse_migration(apps, schema_editor):
    # При откате настройки не удаляем, чтобы не
    # потерять пользовательские значения.
    pass


class Migration(migrations.Migration):
    dependencies = [
        (
            "game",
            "0003_usergenerationsettings_operationgenerationsettings",
        ),
    ]

    operations = [
        migrations.RunPython(
            create_settings,
            reverse_migration,
        ),
    ]