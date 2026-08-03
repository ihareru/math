from django.apps import AppConfig


class SettingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.settings"
    verbose_name = "Настройки пользователя"

    def ready(self):
        from . import signals
