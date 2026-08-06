from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import OperationGenerationSettings, UserGenerationSettings


class AnswerForm(forms.Form):
    answer = forms.IntegerField(
        label="Ваш ответ",
        widget=forms.NumberInput(
            attrs={
                "class": "game-answer-input",
                "autocomplete": "off",
                "inputmode": "numeric",
                "autofocus": True,
                "placeholder": "?",
            }
        ),
    )


class UserGenerationSettingsForm(forms.ModelForm):
    """
    Общие пользовательские настройки генератора.
    """

    class Meta:
        model = UserGenerationSettings

        fields = [
            "avoid_recent_duplicates",
            "recent_questions_limit",
            "auto_increase_difficulty",
            "correct_answers_per_level",
            "maximum_difficulty_level",
        ]

        widgets = {
            "avoid_recent_duplicates": (
                forms.CheckboxInput(
                    attrs={
                        "class": "form-checkbox",
                    }
                )
            ),
            "recent_questions_limit": (
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "min": "1",
                        "max": "500",
                    }
                )
            ),
            "auto_increase_difficulty": (
                forms.CheckboxInput(
                    attrs={
                        "class": "form-checkbox",
                    }
                )
            ),
            "correct_answers_per_level": (
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "min": "1",
                    }
                )
            ),
            "maximum_difficulty_level": (
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "min": "1",
                        "max": "100",
                    }
                )
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        auto_increase = cleaned_data.get(
            "auto_increase_difficulty"
        )

        correct_answers_per_level = (
            cleaned_data.get(
                "correct_answers_per_level"
            )
        )

        maximum_level = cleaned_data.get(
            "maximum_difficulty_level"
        )

        if auto_increase:
            if not correct_answers_per_level:
                self.add_error(
                    "correct_answers_per_level",
                    (
                        "Укажите количество правильных "
                        "ответов до повышения уровня."
                    ),
                )

            if not maximum_level:
                self.add_error(
                    "maximum_difficulty_level",
                    (
                        "Укажите максимальный уровень "
                        "сложности."
                    ),
                )

        return cleaned_data


class OperationGenerationSettingsForm(
    forms.ModelForm
):
    """
    Настройки одного математического действия.
    """

    class Meta:
        model = OperationGenerationSettings

        fields = [
            "is_enabled",
            "mixed_mode_weight",
            "operands_count",
            "first_operand_min",
            "first_operand_max",
            "second_operand_min",
            "second_operand_max",
            "minimum_answer",
            "maximum_answer",
            "allow_negative_result",
        ]

        widgets = {
            "is_enabled": forms.CheckboxInput(
                attrs={
                    "class": "form-checkbox",
                }
            ),
            "mixed_mode_weight": (
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "min": "0",
                        "max": "1000",
                    }
                )
            ),
            "operands_count": forms.Select(
                attrs={
                    "class": "form-control",
                },
                choices=[
                    (2, "2 числа"),
                    (3, "3 числа"),
                    (4, "4 числа"),
                ],
            ),
            "first_operand_min": (
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                    }
                )
            ),
            "first_operand_max": (
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                    }
                )
            ),
            "second_operand_min": (
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                    }
                )
            ),
            "second_operand_max": (
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                    }
                )
            ),
            "minimum_answer": (
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                    }
                )
            ),
            "maximum_answer": (
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                    }
                )
            ),
            "allow_negative_result": (
                forms.CheckboxInput(
                    attrs={
                        "class": "form-checkbox",
                    }
                )
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        operation = (
            self.instance.operation
            if self.instance
            and self.instance.pk
            else None
        )

        if (
            operation
            == OperationGenerationSettings
            .Operation.DIV
        ):
            self.fields[
                "operands_count"
            ].disabled = True

            self.fields[
                "operands_count"
            ].help_text = (
                "Для деления пока поддерживаются "
                "только два числа."
            )

        if (
            operation
            != OperationGenerationSettings
            .Operation.SUB
        ):
            self.fields[
                "allow_negative_result"
            ].disabled = True

            self.fields[
                "allow_negative_result"
            ].help_text = (
                "Доступно только для вычитания."
            )

    def clean(self):
        cleaned_data = super().clean()

        first_min = cleaned_data.get(
            "first_operand_min"
        )

        first_max = cleaned_data.get(
            "first_operand_max"
        )

        second_min = cleaned_data.get(
            "second_operand_min"
        )

        second_max = cleaned_data.get(
            "second_operand_max"
        )

        minimum_answer = cleaned_data.get(
            "minimum_answer"
        )

        maximum_answer = cleaned_data.get(
            "maximum_answer"
        )

        if (
            first_min is not None
            and first_max is not None
            and first_max < first_min
        ):
            self.add_error(
                "first_operand_max",
                (
                    "Максимальное первое число не может "
                    "быть меньше минимального."
                ),
            )

        if (
            second_min is not None
            and second_max is not None
            and second_max < second_min
        ):
            self.add_error(
                "second_operand_max",
                (
                    "Максимальное второе число не может "
                    "быть меньше минимального."
                ),
            )

        if (
            minimum_answer is not None
            and maximum_answer is not None
            and maximum_answer < minimum_answer
        ):
            self.add_error(
                "maximum_answer",
                (
                    "Максимальный результат не может "
                    "быть меньше минимального."
                ),
            )

        operation = self.instance.operation

        allow_negative = cleaned_data.get(
            "allow_negative_result",
            False,
        )

        if (
            operation
            != OperationGenerationSettings
            .Operation.SUB
            and allow_negative
        ):
            self.add_error(
                "allow_negative_result",
                (
                    "Отрицательный результат можно "
                    "разрешить только для вычитания."
                ),
            )

        if (
            operation
            == OperationGenerationSettings
            .Operation.DIV
        ):
            if (
                second_min is not None
                and second_min <= 0
            ):
                self.add_error(
                    "second_operand_min",
                    (
                        "Минимальный делитель должен "
                        "быть больше нуля."
                    ),
                )

            if (
                second_max is not None
                and second_max <= 0
            ):
                self.add_error(
                    "second_operand_max",
                    (
                        "Максимальный делитель должен "
                        "быть больше нуля."
                    ),
                )

        return cleaned_data


class BaseOperationSettingsFormSet(
    BaseInlineFormSet
):
    """
    Общая проверка всех настроек действий.
    """

    def clean(self):
        super().clean()

        if any(
            form.errors
            for form in self.forms
        ):
            return

        enabled_count = 0
        enabled_weight_sum = 0

        for form in self.forms:
            if not hasattr(
                form,
                "cleaned_data",
            ):
                continue

            if form.cleaned_data.get(
                "DELETE",
                False,
            ):
                continue

            is_enabled = form.cleaned_data.get(
                "is_enabled",
                False,
            )

            weight = (
                form.cleaned_data.get(
                    "mixed_mode_weight"
                )
                or 0
            )

            if is_enabled:
                enabled_count += 1
                enabled_weight_sum += weight

        if enabled_count == 0:
            raise ValidationError(
                (
                    "Необходимо включить хотя бы одно "
                    "математическое действие."
                )
            )

        if enabled_weight_sum == 0:
            raise ValidationError(
                (
                    "Хотя бы одно включённое действие "
                    "должно иметь вес больше нуля для "
                    "смешанного режима."
                )
            )


OperationGenerationSettingsFormSet = (
    inlineformset_factory(
        parent_model=UserGenerationSettings,
        model=OperationGenerationSettings,
        form=OperationGenerationSettingsForm,
        formset=BaseOperationSettingsFormSet,
        fields=[
            "is_enabled",
            "mixed_mode_weight",
            "operands_count",
            "first_operand_min",
            "first_operand_max",
            "second_operand_min",
            "second_operand_max",
            "minimum_answer",
            "maximum_answer",
            "allow_negative_result",
        ],
        extra=0,
        can_delete=False,
        min_num=4,
        max_num=4,
        validate_min=True,
        validate_max=True,
    )
)