from django.contrib import admin

from .models import UserSettings


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "background_music",
        "success_sound",
        "fail_sound",
    )

    search_fields = (
        "user__display_name",
        "user__email",
    )
    