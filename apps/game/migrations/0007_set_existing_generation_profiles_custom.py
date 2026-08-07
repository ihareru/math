from django.db import migrations


def mark_existing_profiles_as_custom(
    apps,
    schema_editor,
):
    UserGenerationSettings = apps.get_model(
        "game",
        "UserGenerationSettings",
    )

    UserGenerationSettings.objects.update(
        difficulty_profile="custom",
    )


def reverse_profiles(
    apps,
    schema_editor,
):
    UserGenerationSettings = apps.get_model(
        "game",
        "UserGenerationSettings",
    )

    UserGenerationSettings.objects.update(
        difficulty_profile="medium",
    )


class Migration(migrations.Migration):
    dependencies = [
        (
            "game",
            "0006_usergenerationsettings_difficulty_profile",
        ),
    ]

    operations = [
        migrations.RunPython(
            mark_existing_profiles_as_custom,
            reverse_profiles,
        ),
    ]