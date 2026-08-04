from django import forms


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