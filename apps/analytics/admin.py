from django.contrib import admin

from .models import LoginEvent, VisitSession


@admin.register(VisitSession)
class VisitSessionAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "ip_address",
        "country_name",
        "browser_display",
        "operating_system",
        "device_type",
        "screen_resolution",
        "request_count",
        "first_seen_at",
        "last_seen_at",
    ]

    list_filter = [
        "device_type",
        "browser_name",
        "operating_system",
        "country_code",
        "first_seen_at",
        "last_seen_at",
    ]

    search_fields = [
        "user__display_name",
        "user__email",
        "ip_address",
        "country_name",
        "city_name",
        "browser_name",
        "operating_system",
        "session_key",
    ]

    readonly_fields = [
        "session_key",
        "first_seen_at",
        "last_seen_at",
        "client_context_received_at",
        "request_count",
    ]

    date_hierarchy = "last_seen_at"

    fieldsets = [
        (
            "Пользователь и сессия",
            {
                "fields": [
                    "user",
                    "session_key",
                    "first_seen_at",
                    "last_seen_at",
                    "request_count",
                    "last_path",
                ]
            },
        ),
        (
            "Сеть и география",
            {
                "fields": [
                    "ip_address",
                    "country_code",
                    "country_name",
                    "city_name",
                ]
            },
        ),
        (
            "Браузер и устройство",
            {
                "fields": [
                    "browser_name",
                    "browser_version",
                    "operating_system",
                    "device_type",
                    "user_agent",
                ]
            },
        ),
        (
            "Экран и браузерный контекст",
            {
                "fields": [
                    "screen_width",
                    "screen_height",
                    "viewport_width",
                    "viewport_height",
                    "pixel_ratio",
                    "browser_language",
                    "timezone_name",
                    "touch_points",
                    "cpu_cores",
                    "client_context_received_at",
                ]
            },
        ),
    ]


@admin.register(LoginEvent)
class LoginEventAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "ip_address",
        "country_name",
        "browser_name",
        "browser_version",
        "operating_system",
        "device_type",
        "logged_in_at",
    ]

    list_filter = [
        "device_type",
        "browser_name",
        "operating_system",
        "country_code",
        "logged_in_at",
    ]

    search_fields = [
        "user__display_name",
        "user__email",
        "ip_address",
        "country_name",
        "city_name",
    ]

    readonly_fields = [
        "user",
        "visit_session",
        "ip_address",
        "user_agent",
        "browser_name",
        "browser_version",
        "operating_system",
        "device_type",
        "country_code",
        "country_name",
        "city_name",
        "logged_in_at",
    ]

    date_hierarchy = "logged_in_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return False