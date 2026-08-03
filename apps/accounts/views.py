from django.contrib import messages
from django.contrib.auth import (
    login as auth_login,
    logout as auth_logout,
)
from django.contrib.auth.decorators import (
    login_required,
)
from django.db import transaction
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.urls import reverse

from .forms import (
    AccountProfileForm,
    LoginForm,
    PasswordResetRequestForm,
    RegistrationForm,
    ResumeRegistrationForm,
    SetNewPasswordForm,
    VerificationCodeForm,
)
from .models import User
from .services.verification import (
    VerificationError,
    VerificationResendTooEarlyError,
    create_password_reset_code,
    create_registration_code,
    verify_password_reset_code,
    verify_registration_code,
)


PENDING_USER_SESSION_KEY = (
    "pending_registration_user_id"
)

PASSWORD_RESET_USER_SESSION_KEY = (
    "password_reset_user_id"
)

PASSWORD_RESET_VERIFIED_SESSION_KEY = (
    "password_reset_verified"
)


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    create_registration_code(user)

            except VerificationError as error:
                messages.error(
                    request,
                    str(error),
                )

                return render(
                    request,
                    "accounts/register.html",
                    {
                        "form": form,
                    },
                )

            request.session[
                PENDING_USER_SESSION_KEY
            ] = str(user.pk)

            messages.success(
                request,
                (
                    "Мы отправили код подтверждения. "
                    "Введите его на следующей странице."
                ),
            )

            return redirect(
                "accounts:verify_registration"
            )
    else:
        form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


def verify_registration(request):
    user_id = request.session.get(
        PENDING_USER_SESSION_KEY
    )

    if not user_id:
        messages.warning(
            request,
            "Сначала заполните форму регистрации.",
        )
        return redirect("accounts:register")

    user = get_object_or_404(
        User,
        pk=user_id,
    )

    if user.registration_confirmed:
        user.is_active = True
        user.save(
            update_fields=[
                "is_active",
            ]
        )

        request.session.pop(
            PENDING_USER_SESSION_KEY,
            None,
        )

        messages.info(
            request,
            "Регистрация уже подтверждена.",
        )

        return redirect("accounts:login")

    if request.method == "POST":
        form = VerificationCodeForm(request.POST)

        if form.is_valid():
            try:
                verify_registration_code(
                    user=user,
                    raw_code=form.cleaned_data[
                        "code"
                    ],
                )

            except VerificationError as error:
                form.add_error(
                    "code",
                    str(error),
                )
            else:
                request.session.pop(
                    PENDING_USER_SESSION_KEY,
                    None,
                )

                messages.success(
                    request,
                    (
                        "Регистрация подтверждена. "
                        "Теперь вы можете войти."
                    ),
                )

                return redirect("accounts:login")
    else:
        form = VerificationCodeForm()

    return render(
        request,
        "accounts/verify_registration.html",
        {
            "form": form,
            "pending_user": user,
        },
    )


def resend_registration_code(request):
    if request.method != "POST":
        return redirect(
            "accounts:verify_registration"
        )

    user_id = request.session.get(
        PENDING_USER_SESSION_KEY
    )

    if not user_id:
        messages.warning(
            request,
            "Сначала заполните форму регистрации.",
        )
        return redirect("accounts:register")

    user = get_object_or_404(
        User,
        pk=user_id,
    )

    try:
        create_registration_code(user)

    except VerificationResendTooEarlyError as error:
        messages.warning(
            request,
            str(error),
        )

    except VerificationError as error:
        messages.error(
            request,
            str(error),
        )

    else:
        messages.success(
            request,
            "Новый код подтверждения отправлен.",
        )

    return redirect(
        "accounts:verify_registration"
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = LoginForm(
            request.POST,
            request=request,
        )

        if form.is_valid():
            user = form.get_user()

            auth_login(
                request,
                user,
            )

            if form.cleaned_data["remember_me"]:
                request.session.set_expiry(
                    60 * 60 * 24 * 30
                )
            else:
                request.session.set_expiry(0)

            messages.success(
                request,
                f"Добро пожаловать, {user.display_name}!",
            )

            next_url = request.POST.get("next")

            if next_url:
                return redirect(next_url)

            return redirect("dashboard:home")
    else:
        form = LoginForm(
            request=request,
        )

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "next": request.GET.get("next", ""),
        },
    )


@login_required
def logout_view(request):
    if request.method == "POST":
        auth_logout(request)

        messages.success(
            request,
            "Вы вышли из учётной записи.",
        )

    return redirect("dashboard:home")

def resume_registration(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = ResumeRegistrationForm(
            request.POST,
        )

        if form.is_valid():
            email = form.cleaned_data["email"]

            user = (
                User.objects
                .filter(
                    email__iexact=email,
                    is_active=False,
                    email_verified=False,
                )
                .first()
            )

            if user is not None:
                try:
                    create_registration_code(user)

                except VerificationResendTooEarlyError as error:
                    messages.warning(
                        request,
                        str(error),
                    )

                except VerificationError as error:
                    messages.error(
                        request,
                        str(error),
                    )

                else:
                    request.session[
                        PENDING_USER_SESSION_KEY
                    ] = str(user.pk)

                    messages.success(
                        request,
                        (
                            "Новый код подтверждения "
                            "отправлен на email."
                        ),
                    )

                    return redirect(
                        "accounts:verify_registration"
                    )

            # Не сообщаем, существует ли такой email.
            messages.info(
                request,
                (
                    "Если для этого email существует "
                    "незавершённая регистрация, "
                    "мы отправили новый код."
                ),
            )

            return redirect(
                "accounts:login"
            )
    else:
        form = ResumeRegistrationForm()

    return render(
        request,
        "accounts/resume_registration.html",
        {
            "form": form,
        },
    )

def password_reset_request(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = PasswordResetRequestForm(
            request.POST,
        )

        if form.is_valid():
            email = form.cleaned_data["email"]

            user = (
                User.objects
                .filter(
                    email__iexact=email,
                    is_active=True,
                    email_verified=True,
                )
                .first()
            )

            if user is not None:
                try:
                    create_password_reset_code(user)

                except VerificationResendTooEarlyError as error:
                    messages.warning(
                        request,
                        str(error),
                    )

                    request.session[
                        PASSWORD_RESET_USER_SESSION_KEY
                    ] = str(user.pk)

                    return redirect(
                        "accounts:password_reset_verify"
                    )

                except VerificationError:
                    messages.error(
                        request,
                        (
                            "Не удалось отправить код. "
                            "Попробуйте позже."
                        ),
                    )
                else:
                    request.session[
                        PASSWORD_RESET_USER_SESSION_KEY
                    ] = str(user.pk)

                    request.session[
                        PASSWORD_RESET_VERIFIED_SESSION_KEY
                    ] = False

                    messages.success(
                        request,
                        (
                            "Код восстановления отправлен "
                            "на ваш email."
                        ),
                    )

                    return redirect(
                        "accounts:password_reset_verify"
                    )

            # Одинаковое сообщение для существующего
            # и несуществующего email.
            messages.info(
                request,
                (
                    "Если аккаунт с таким email существует, "
                    "на него отправлена инструкция."
                ),
            )

            return redirect(
                "accounts:login"
            )
    else:
        form = PasswordResetRequestForm()

    return render(
        request,
        "accounts/password_reset_request.html",
        {
            "form": form,
        },
    )

def password_reset_verify(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    user_id = request.session.get(
        PASSWORD_RESET_USER_SESSION_KEY
    )

    if not user_id:
        messages.warning(
            request,
            (
                "Сначала запросите код "
                "восстановления пароля."
            ),
        )

        return redirect(
            "accounts:password_reset_request"
        )

    user = get_object_or_404(
        User,
        pk=user_id,
        is_active=True,
        email_verified=True,
    )

    if request.method == "POST":
        form = VerificationCodeForm(
            request.POST,
        )

        if form.is_valid():
            try:
                verify_password_reset_code(
                    user=user,
                    raw_code=form.cleaned_data[
                        "code"
                    ],
                )

            except VerificationError as error:
                form.add_error(
                    "code",
                    str(error),
                )

            else:
                request.session[
                    PASSWORD_RESET_VERIFIED_SESSION_KEY
                ] = True

                return redirect(
                    "accounts:password_reset_confirm"
                )
    else:
        form = VerificationCodeForm()

    return render(
        request,
        "accounts/password_reset_verify.html",
        {
            "form": form,
            "reset_user": user,
        },
    )

def password_reset_confirm(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    user_id = request.session.get(
        PASSWORD_RESET_USER_SESSION_KEY
    )

    reset_verified = request.session.get(
        PASSWORD_RESET_VERIFIED_SESSION_KEY,
        False,
    )

    if not user_id or not reset_verified:
        messages.warning(
            request,
            (
                "Необходимо подтвердить код "
                "восстановления."
            ),
        )

        return redirect(
            "accounts:password_reset_request"
        )

    user = get_object_or_404(
        User,
        pk=user_id,
        is_active=True,
    )

    if request.method == "POST":
        form = SetNewPasswordForm(
            request.POST,
            user=user,
        )

        if form.is_valid():
            user.set_password(
                form.cleaned_data["password1"]
            )

            user.save(
                update_fields=[
                    "password",
                ]
            )

            # Завершаем все текущие шаги восстановления.
            request.session.pop(
                PASSWORD_RESET_USER_SESSION_KEY,
                None,
            )

            request.session.pop(
                PASSWORD_RESET_VERIFIED_SESSION_KEY,
                None,
            )

            messages.success(
                request,
                (
                    "Пароль успешно изменён. "
                    "Теперь войдите с новым паролем."
                ),
            )

            return redirect(
                "accounts:login"
            )
    else:
        form = SetNewPasswordForm(
            user=user,
        )

    return render(
        request,
        "accounts/password_reset_confirm.html",
        {
            "form": form,
        },
    )

def password_reset_resend(request):
    if request.method != "POST":
        return redirect(
            "accounts:password_reset_request"
        )

    user_id = request.session.get(
        PASSWORD_RESET_USER_SESSION_KEY
    )

    if not user_id:
        return redirect(
            "accounts:password_reset_request"
        )

    user = get_object_or_404(
        User,
        pk=user_id,
        is_active=True,
        email_verified=True,
    )

    try:
        create_password_reset_code(user)

    except VerificationResendTooEarlyError as error:
        messages.warning(
            request,
            str(error),
        )

    except VerificationError:
        messages.error(
            request,
            "Не удалось отправить код.",
        )

    else:
        messages.success(
            request,
            "Новый код отправлен на email.",
        )

    return redirect(
        "accounts:password_reset_verify"
    )

@login_required
def account_detail(request):
    return render(
        request,
        "accounts/account_detail.html",
    )

@login_required
def account_edit(request):
    if request.method == "POST":
        form = AccountProfileForm(
            request.POST,
            instance=request.user,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Настройки профиля сохранены.",
            )

            return redirect(
                "accounts:account_detail"
            )
    else:
        form = AccountProfileForm(
            instance=request.user,
        )

    return render(
        request,
        "accounts/account_edit.html",
        {
            "form": form,
        },
    )

