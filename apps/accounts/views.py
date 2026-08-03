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
    LoginForm,
    RegistrationForm,
    VerificationCodeForm,
)
from .models import User
from .services.verification import (
    VerificationError,
    VerificationResendTooEarlyError,
    create_registration_code,
    verify_registration_code,
)


PENDING_USER_SESSION_KEY = (
    "pending_registration_user_id"
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