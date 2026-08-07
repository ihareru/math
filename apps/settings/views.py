from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import UserSettingsForm
from .models import UserSettings


ALLOWED_BACKGROUND_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def get_background_choices():
    backgrounds_dir = (
        Path(settings.BASE_DIR)
        / "static"
        / "backgrounds"
    )

    if not backgrounds_dir.exists():
        return []

    files = []

    for path in backgrounds_dir.iterdir():
        if (
            path.is_file()
            and path.suffix.lower()
            in ALLOWED_BACKGROUND_EXTENSIONS
        ):
            files.append(path.name)

    files.sort(key=str.lower)

    return [
        (filename, filename)
        for filename in files
    ]


@login_required
def user_settings(request):
    settings_object, _ = (
        UserSettings.objects.get_or_create(
            user=request.user,
        )
    )

    background_choices = get_background_choices()

    if request.method == "POST":
        form = UserSettingsForm(
            request.POST,
            instance=settings_object,
            background_choices=background_choices,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Настройки сохранены.",
            )

            return redirect(
                "user_settings:detail"
            )
    else:
        form = UserSettingsForm(
            instance=settings_object,
            background_choices=background_choices,
        )

    return render(
        request,
        "settings/user_settings.html",
        {
            "form": form,
        },
    )