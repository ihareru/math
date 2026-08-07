from django.contrib import admin

from .models import (
    CheatCode,
    CheatReward,
    UserCheat,
)


class CheatRewardInline(admin.TabularInline):
    model = CheatReward
    extra = 1

    fields = [
        "reward_type",
        "reward_data",
    ]

    show_change_link = True


@admin.register(CheatCode)
class CheatCodeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "code",
        "is_active",
        "activation_status",
        "valid_from",
        "valid_until",
        "duration_days",
        "activation_count",
        "max_global_activations",
        "max_user_activations",
    ]

    list_filter = [
        "is_active",
        "valid_from",
        "valid_until",
    ]

    search_fields = [
        "name",
        "code",
        "description",
    ]

    readonly_fields = [
        "activation_count",
        "created_at",
        "updated_at",
    ]

    date_hierarchy = "created_at"

    inlines = [
        CheatRewardInline,
    ]

    fieldsets = [
        (
            "Основные данные",
            {
                "fields": [
                    "name",
                    "code",
                    "description",
                    "is_active",
                ],
            },
        ),
        (
            "Сроки",
            {
                "fields": [
                    "valid_from",
                    "valid_until",
                    "duration_days",
                ],
            },
        ),
        (
            "Ограничения",
            {
                "fields": [
                    "max_global_activations",
                    "max_user_activations",
                    "activation_count",
                ],
            },
        ),
        (
            "Служебные данные",
            {
                "fields": [
                    "created_at",
                    "updated_at",
                ],
            },
        ),
    ]

    @admin.display(
        boolean=True,
        description="Доступен для активации",
    )
    def activation_status(self, obj):
        return obj.activation_is_available


@admin.register(CheatReward)
class CheatRewardAdmin(admin.ModelAdmin):
    list_display = [
        "cheat",
        "reward_type",
        "reward_data",
        "created_at",
    ]

    list_filter = [
        "reward_type",
        "created_at",
    ]

    search_fields = [
        "cheat__name",
        "cheat__code",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]


@admin.register(UserCheat)
class UserCheatAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "cheat",
        "activated_at",
        "expires_at",
        "is_active",
        "current_status",
        "activation_ip",
    ]

    list_filter = [
        "is_active",
        "cheat",
        "activated_at",
        "expires_at",
    ]

    search_fields = [
        "user__display_name",
        "user__email",
        "cheat__name",
        "cheat__code",
        "activation_ip",
    ]

    readonly_fields = [
        "user",
        "cheat",
        "activated_at",
        "expires_at",
        "activation_ip",
        "activation_user_agent",
        "created_at",
    ]

    date_hierarchy = "activated_at"

    def has_add_permission(self, request):
        # Активации должны создаваться только сервисом,
        # чтобы корректно проверялись лимиты.
        return False

    @admin.display(
        boolean=True,
        description="Действует сейчас",
    )
    def current_status(self, obj):
        return obj.currently_active