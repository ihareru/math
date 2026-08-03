from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, VerificationCode


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = [
        "-date_joined",
    ]

    list_display = [
        "display_name",
        "email",
        "registration_method",
        "email_verified",
        "is_active",
        "is_staff",
        "date_joined",
    ]

    list_filter = [
        "registration_method",
        "email_verified",
        "show_in_rating",
        "is_active",
        "is_staff",
        "is_superuser",
    ]

    search_fields = [
        "display_name",
        "email",
        "phone",
    ]

    readonly_fields = [
        "id",
        "date_joined",
        "last_login",
        "last_activity_at",
    ]

    fieldsets = [
        (
            None,
            {
                "fields": [
                    "id",
                    "email",
                    "phone",
                    "password",
                ]
            },
        ),
        (
            "Публичные данные",
            {
                "fields": [
                    "display_name",
                    "show_in_rating",
                ]
            },
        ),
        (
            "Регистрация и подтверждение",
            {
                "fields": [
                    "registration_method",
                    "email_verified",
                    "phone_verified",
                ]
            },
        ),
        (
            _("Permissions"),
            {
                "fields": [
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ]
            },
        ),
        (
            _("Important dates"),
            {
                "fields": [
                    "last_login",
                    "date_joined",
                    "last_activity_at",
                ]
            },
        ),
    ]

    add_fieldsets = [
        (
            None,
            {
                "classes": [
                    "wide",
                ],
                "fields": [
                    "email",
                    "phone",
                    "display_name",
                    "registration_method",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                ],
            },
        ),
    ]


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "purpose",
        "delivery_method",
        "destination",
        "created_at",
        "expires_at",
        "attempts",
        "used_at",
    ]

    list_filter = [
        "purpose",
        "delivery_method",
        "created_at",
        "expires_at",
        "used_at",
    ]

    search_fields = [
        "user__display_name",
        "user__email",
        "user__phone",
        "destination",
    ]

    readonly_fields = [
        "id",
        "user",
        "purpose",
        "delivery_method",
        "code_hash",
        "destination",
        "expires_at",
        "attempts",
        "max_attempts",
        "used_at",
        "created_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return False