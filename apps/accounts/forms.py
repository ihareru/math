from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import (
    validate_password,
)
from django.core.exceptions import ValidationError

from .models import User


class StyledFormMixin:
    def apply_styles(self):
        for field in self.fields.values():
            existing_class = (
                field.widget.attrs.get("class", "")
            )

            field.widget.attrs["class"] = (
                f"{existing_class} form-control"
            ).strip()


class RegistrationForm(
    StyledFormMixin,
    forms.Form,
):
    display_name = forms.CharField(
        label="Имя в рейтинге",
        max_length=100,
        help_text=(
            "Это имя будет видно другим пользователям "
            "в публичном рейтинге."
        ),
    )

    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "name@example.com",
            }
        ),
    )

    password1 = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
            }
        ),
        help_text=(
            "Минимум 8 символов. "
            "Не используйте слишком простой пароль."
        ),
    )

    password2 = forms.CharField(
        label="Повторите пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
            }
        ),
    )

    show_in_rating = forms.BooleanField(
        label="Показывать меня в общем рейтинге",
        required=False,
        initial=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()

    def clean_email(self):
        email = self.cleaned_data["email"]
        email = email.strip().lower()

        if User.objects.filter(
            email__iexact=email,
        ).exists():
            raise forms.ValidationError(
                "Пользователь с таким email уже существует."
            )

        return email

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2:
            if password1 != password2:
                self.add_error(
                    "password2",
                    "Пароли не совпадают.",
                )
            else:
                try:
                    validate_password(password1)
                except ValidationError as error:
                    self.add_error(
                        "password1",
                        error,
                    )

        return cleaned_data

    def save(self):
        if not self.is_valid():
            raise ValueError(
                "Нельзя сохранить невалидную форму."
            )

        return User.objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
            display_name=self.cleaned_data[
                "display_name"
            ],
            registration_method=(
                User.RegistrationMethod.EMAIL
            ),
            show_in_rating=self.cleaned_data[
                "show_in_rating"
            ],
            is_active=False,
            email_verified=False,
            phone_verified=False,
        )


class VerificationCodeForm(
    StyledFormMixin,
    forms.Form,
):
    code = forms.CharField(
        label="Код подтверждения",
        min_length=6,
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "pattern": "[0-9]{6}",
                "placeholder": "000000",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()

    def clean_code(self):
        code = self.cleaned_data["code"].strip()

        if not code.isdigit():
            raise forms.ValidationError(
                "Код должен состоять из шести цифр."
            )

        return code


class LoginForm(
    StyledFormMixin,
    forms.Form,
):
    identifier = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "name@example.com",
            }
        ),
    )

    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": (
                    "current-password"
                ),
            }
        ),
    )

    remember_me = forms.BooleanField(
        label="Запомнить меня",
        required=False,
        initial=False,
    )

    def __init__(
        self,
        *args,
        request=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.request = request
        self.user = None

        self.apply_styles()

    def clean(self):
        cleaned_data = super().clean()

        identifier = cleaned_data.get("identifier")
        password = cleaned_data.get("password")

        if not identifier or not password:
            return cleaned_data

        self.user = authenticate(
            request=self.request,
            identifier=identifier,
            password=password,
        )

        if self.user is None:
            possible_user = (
                User.objects
                .filter(
                    email__iexact=identifier.strip().lower()
                )
                .first()
            )

            if (
                    possible_user
                    and not possible_user.is_active
                    and not possible_user.registration_confirmed
            ):
                raise forms.ValidationError(
                    "Регистрация не подтверждена. "
                    "Запросите новый код подтверждения."
                )

            raise forms.ValidationError(
                "Неверный email или пароль."
            )

        return cleaned_data

    def get_user(self):
        return self.user

class ResumeRegistrationForm(
    StyledFormMixin,
    forms.Form,
):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "name@example.com",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()

    def clean_email(self):
        return (
            self.cleaned_data["email"]
            .strip()
            .lower()
        )


class PasswordResetRequestForm(
    StyledFormMixin,
    forms.Form,
):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "name@example.com",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()

    def clean_email(self):
        return (
            self.cleaned_data["email"]
            .strip()
            .lower()
        )


class SetNewPasswordForm(
    StyledFormMixin,
    forms.Form,
):
    password1 = forms.CharField(
        label="Новый пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
            }
        ),
    )

    password2 = forms.CharField(
        label="Повторите новый пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
            }
        ),
    )

    def __init__(
        self,
        *args,
        user=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.user = user
        self.apply_styles()

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if not password1 or not password2:
            return cleaned_data

        if password1 != password2:
            self.add_error(
                "password2",
                "Пароли не совпадают.",
            )

            return cleaned_data

        try:
            validate_password(
                password1,
                user=self.user,
            )
        except ValidationError as error:
            self.add_error(
                "password1",
                error,
            )

        return cleaned_data


class AccountProfileForm(
    StyledFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = User

        fields = [
            "display_name",
            "show_in_rating",
        ]

        labels = {
            "display_name": "Имя в рейтинге",
            "show_in_rating": (
                "Показывать меня в общем рейтинге"
            ),
        }

        help_texts = {
            "display_name": (
                "Это имя будет видно другим пользователям "
                "на публичной странице рейтинга."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()