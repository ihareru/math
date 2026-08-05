from django import forms


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