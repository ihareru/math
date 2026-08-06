from django.contrib import admin

from .models import (
    GameQuestion,
    GameSession,
    OperationGenerationSettings,
    StarTransaction,
    UserGameStatistics,
    UserGenerationSettings,
)


@admin.register(UserGameStatistics)
class UserGameStatisticsAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "stars",
        "total_correct",
        "total_wrong",
        "best_streak",
        "total_sessions",
        "accuracy",
    ]

    search_fields = [
        "user__display_name",
        "user__email",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]

    def accuracy(self, obj):
        return f"{obj.accuracy_percent} %"

    accuracy.short_description = "Точность"


class GameQuestionInline(admin.TabularInline):
    model = GameQuestion
    extra = 0

    fields = [
        "sequence_number",
        "operation",
        "num1",
        "num2",
        "user_answer",
        "correct_answer",
        "is_correct",
        "response_time_ms",
        "is_review",
    ]

    readonly_fields = fields

    can_delete = False
    show_change_link = True


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "mode",
        "status",
        "correct_count",
        "wrong_count",
        "best_streak",
        "stars_earned",
        "started_at",
        "finished_at",
    ]

    list_filter = [
        "mode",
        "status",
        "started_at",
    ]

    search_fields = [
        "user__display_name",
        "user__email",
    ]

    readonly_fields = [
        "started_at",
        "last_activity_at",
        "finished_at",
    ]

    inlines = [
        GameQuestionInline,
    ]


@admin.register(GameQuestion)
class GameQuestionAdmin(admin.ModelAdmin):
    list_display = [
        "session",
        "sequence_number",
        "expression_display",
        "user_answer",
        "correct_answer",
        "is_correct",
        "response_time_ms",
        "is_review",
        "answered_at",
    ]

    list_filter = [
        "operation",
        "is_correct",
        "is_review",
        "answered_at",
    ]

    search_fields = [
        "session__user__display_name",
        "session__user__email",
    ]

    readonly_fields = [
        "shown_at",
        "answered_at",
    ]

    def expression_display(self, obj):
        return obj.expression

    expression_display.short_description = "Пример"


@admin.register(StarTransaction)
class StarTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "amount",
        "reason",
        "description",
        "session",
        "created_at",
    ]

    list_filter = [
        "reason",
        "created_at",
    ]

    search_fields = [
        "user__display_name",
        "user__email",
        "description",
    ]

    readonly_fields = [
        "created_at",
    ]


class OperationGenerationSettingsInline(
    admin.TabularInline
):
    model = OperationGenerationSettings
    extra = 0

    fields = [
        "operation",
        "is_enabled",
        "mixed_mode_weight",
        "first_operand_min",
        "first_operand_max",
        "second_operand_min",
        "second_operand_max",
        "operands_count",
        "minimum_answer",
        "maximum_answer",
        "allow_negative_result",
        "allow_remainder",
    ]


@admin.register(UserGenerationSettings)
class UserGenerationSettingsAdmin(
    admin.ModelAdmin
):
    list_display = [
        "user",
        "avoid_recent_duplicates",
        "recent_questions_limit",
        "auto_increase_difficulty",
        "difficulty_level",
    ]

    list_filter = [
        "avoid_recent_duplicates",
        "auto_increase_difficulty",
    ]

    search_fields = [
        "user__display_name",
        "user__email",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]

    inlines = [
        OperationGenerationSettingsInline,
    ]

    @admin.display(
        description="Текущий уровень",
    )
    def difficulty_level(self, obj):
        return obj.current_difficulty_level


@admin.register(OperationGenerationSettings)
class OperationGenerationSettingsAdmin(
    admin.ModelAdmin
):
    list_display = [
        "generation_settings",
        "operation",
        "is_enabled",
        "mixed_mode_weight",
        "first_operand_min",
        "first_operand_max",
        "second_operand_min",
        "second_operand_max",
    ]

    list_filter = [
        "operation",
        "is_enabled",
    ]

    search_fields = [
        "generation_settings__user__display_name",
        "generation_settings__user__email",
    ]


