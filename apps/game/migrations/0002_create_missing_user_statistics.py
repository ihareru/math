from django.conf import settings
from django.db import migrations


def create_missing_user_statistics(
    apps,
    schema_editor,
):
    User = apps.get_model(
        settings.AUTH_USER_MODEL,
    )

    UserGameStatistics = apps.get_model(
        "game",
        "UserGameStatistics",
    )

    for user in User.objects.iterator():
        UserGameStatistics.objects.get_or_create(
            user_id=user.pk,
        )


def reverse_migration(
    apps,
    schema_editor,
):
    # При откате записи не удаляем,
    # чтобы случайно не потерять статистику.
    pass


class Migration(migrations.Migration):
    dependencies = [
        (
            "game",
            "0001_initial",
        ),
    ]

    operations = [
        migrations.RunPython(
            create_missing_user_statistics,
            reverse_migration,
        ),
    ]