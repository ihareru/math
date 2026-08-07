from pathlib import Path

from django.conf import settings as django_settings
from django.templatetags.static import static

from .models import UserSettings


ALLOWED_BACKGROUND_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def _get_default_settings():
    """
    Настройки оформления для анонимного пользователя
    или на случай отсутствия записи в базе.
    """
    return {
        "background_color": "#87CEEB",
        "background_image": "",
        "background_image_url": "",
        "background_music": False,
        "success_sound": True,
        "fail_sound": True,
        "background_volume": 50,
        "success_volume": 50,
        "fail_volume": 50,
    }


def _get_background_url(filename):
    """
    Возвращает URL только для допустимого файла,
    действительно существующего в static/backgrounds.
    """
    if not filename:
        return ""

    safe_filename = Path(filename).name

    if safe_filename != filename:
        return ""

    suffix = Path(safe_filename).suffix.lower()

    if suffix not in ALLOWED_BACKGROUND_EXTENSIONS:
        return ""

    background_file = (
        Path(django_settings.BASE_DIR)
        / "static"
        / "backgrounds"
        / safe_filename
    )

    if not background_file.is_file():
        return ""

    return static(
        f"backgrounds/{safe_filename}"
    )


def user_game_settings(request):
    """
    Добавляет индивидуальные игровые настройки
    в контекст каждого шаблона.
    """
    context = _get_default_settings()

    if not request.user.is_authenticated:
        return {
            "game_settings": context,
        }

    settings_object, _ = (
        UserSettings.objects.get_or_create(
            user=request.user,
        )
    )

    context.update(
        {
            "background_color": (
                settings_object.background_color
            ),
            "background_image": (
                settings_object.background_image
            ),
            "background_image_url": (
                _get_background_url(
                    settings_object.background_image
                )
            ),
            "background_music": (
                settings_object.background_music
            ),
            "success_sound": (
                settings_object.success_sound
            ),
            "fail_sound": (
                settings_object.fail_sound
            ),
            "background_volume": (
                settings_object.background_volume
            ),
            "success_volume": (
                settings_object.success_volume
            ),
            "fail_volume": (
                settings_object.fail_volume
            ),
        }
    )

    return {
        "game_settings": context,
    }