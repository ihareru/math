from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator

from .models import UserSettings


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings

        fields = [
            "background_color",
            "background_image",
            "background_music",
            "success_sound",
            "fail_sound",
            "background_volume",
            "success_volume",
            "fail_volume",
        ]

        labels = {
            "background_color": "Цвет фона",
            "background_image": "Фоновое изображение",
            "background_music": "Фоновая музыка",
            "success_sound": "Звук правильного ответа",
            "fail_sound": "Звук неправильного ответа",
            "background_volume": "Громкость фоновой музыки",
            "success_volume": "Громкость правильного ответа",
            "fail_volume": "Громкость неправильного ответа",
        }

        widgets = {
            "background_color": forms.TextInput(
                attrs={
                    "type": "color",
                    "class": "form-control form-control--color",
                }
            ),
            "background_image": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "background_music": forms.CheckboxInput(),
            "success_sound": forms.CheckboxInput(),
            "fail_sound": forms.CheckboxInput(),
            "background_volume": forms.NumberInput(
                attrs={
                    "type": "range",
                    "min": "0",
                    "max": "100",
                    "step": "1",
                    "class": "volume-range",
                }
            ),
            "success_volume": forms.NumberInput(
                attrs={
                    "type": "range",
                    "min": "0",
                    "max": "100",
                    "step": "1",
                    "class": "volume-range",
                }
            ),
            "fail_volume": forms.NumberInput(
                attrs={
                    "type": "range",
                    "min": "0",
                    "max": "100",
                    "step": "1",
                    "class": "volume-range",
                }
            ),
        }

    def __init__(self, *args, background_choices=None, **kwargs):
        super().__init__(*args, **kwargs)

        choices = [
            ("", "Без фонового изображения"),
        ]

        if background_choices:
            choices.extend(background_choices)

        self.fields["background_image"].widget = forms.Select(
            choices=choices,
            attrs={
                "class": "form-control",
            },
        )

        for field_name in (
            "background_volume",
            "success_volume",
            "fail_volume",
        ):
            self.fields[field_name].validators = [
                MinValueValidator(0),
                MaxValueValidator(100),
            ]