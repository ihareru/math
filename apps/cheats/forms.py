from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from .models import (
    CheatCode,
    CheatReward,
)


class CheatActivationForm(forms.Form):
    code = forms.CharField(
        label="Секретный код",
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "class": "form-control cheat-code-input",
                "autocomplete": "off",
                "autocapitalize": "characters",
                "spellcheck": "false",
                "placeholder": "Введите код",
            }
        ),
    )

    def clean_code(self):
        return (
            self.cleaned_data["code"]
            .strip()
            .upper()
        )


class CheatCodeAdminForm(forms.ModelForm):
    class Meta:
        model = CheatCode

        fields = [
            "name",
            "code",
            "description",
            "is_active",
            "valid_from",
            "valid_until",
            "duration_days",
            "max_global_activations",
            "max_user_activations",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "code": forms.TextInput(
                attrs={
                    "class": (
                        "form-control cheat-code-input"
                    ),
                    "autocomplete": "off",
                    "spellcheck": "false",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                }
            ),
            "valid_from": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "valid_until": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "duration_days": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                }
            ),
            "max_global_activations": (
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "min": "1",
                    }
                )
            ),
            "max_user_activations": (
                forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "min": "1",
                    }
                )
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["valid_from"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]

        self.fields["valid_until"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]

    def clean_code(self):
        code = self.cleaned_data["code"]
        code = code.strip().upper()

        if any(character.isspace() for character in code):
            raise ValidationError(
                "Код не должен содержать пробелы."
            )

        return code


class CheatRewardAdminForm(forms.ModelForm):
    class Meta:
        model = CheatReward

        fields = [
            "reward_type",
            "reward_data",
        ]

        widgets = {
            "reward_type": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "reward_data": forms.Textarea(
                attrs={
                    "class": (
                        "form-control reward-json-input"
                    ),
                    "rows": 5,
                    "spellcheck": "false",
                }
            ),
        }

        help_texts = {
            "reward_data": (
                'Например: {"answers": 8}, '
                '{"multiplier": 2}, '
                '{"enabled": true}.'
            ),
        }


class ActivationFilterForm(forms.Form):
    search = forms.CharField(
        label="Поиск",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": (
                    "Имя, email или код"
                ),
            }
        ),
    )

    status = forms.ChoiceField(
        label="Статус",
        required=False,
        choices=[
            ("", "Все"),
            ("active", "Действующие"),
            ("expired", "Истёкшие"),
            ("disabled", "Отключённые"),
        ],
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )


CheatRewardFormSet = inlineformset_factory(
    parent_model=CheatCode,
    model=CheatReward,
    form=CheatRewardAdminForm,
    fields=[
        "reward_type",
        "reward_data",
    ],
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)