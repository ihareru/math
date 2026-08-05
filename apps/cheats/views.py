from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
)
from django.shortcuts import redirect, render
from django.views.decorators.http import (
    require_POST,
)

from apps.analytics.services.client import (
    get_client_ip,
)

from .forms import CheatActivationForm
from .services.activation import (
    activate_cheat_code,
)
from .services.exceptions import (
    CheatActivationError,
)
from .services.rewards import (
    get_active_game_rewards,
    get_active_user_cheats,
)
from .models import UserCheat


@login_required
def cheat_codes(request):
    active_activations = list(
        get_active_user_cheats(
            user=request.user,
        )
    )
    activation_history = (
        UserCheat.objects
        .filter(user=request.user)
        .select_related("cheat")
        .order_by("-activated_at")[:50]
    )

    active_rewards = get_active_game_rewards(
        user=request.user,
    )

    return render(
        request,
        "cheats/cheat_codes.html",
        {
            "form": CheatActivationForm(),
            "active_activations": (
                active_activations
            ),
            "active_rewards": active_rewards,
            "activation_history": activation_history,
        },
    )


@login_required
@require_POST
def activate(request):
    form = CheatActivationForm(
        request.POST,
    )

    if not form.is_valid():
        active_activations = list(
            get_active_user_cheats(
                user=request.user,
            )
        )
        activation_history = (
            UserCheat.objects
            .filter(user=request.user)
            .select_related("cheat")
            .order_by("-activated_at")[:50]
        )

        return render(
            request,
            "cheats/cheat_codes.html",
            {
                "form": form,
                "active_activations": (
                    active_activations
                ),
                "active_rewards": (
                    get_active_game_rewards(
                        user=request.user,
                    )
                ),
                "activation_history": (
                    activation_history
                ),
            },
            status=400,
        )

    try:
        result = activate_cheat_code(
            user=request.user,
            raw_code=form.cleaned_data[
                "code"
            ],
            activation_ip=get_client_ip(
                request
            ),
            activation_user_agent=(
                request.META.get(
                    "HTTP_USER_AGENT",
                    "",
                )
            ),
        )

    except CheatActivationError as error:
        messages.error(
            request,
            str(error),
        )

    else:
        message = (
            f"Код {result.cheat.code} "
            "успешно активирован."
        )

        if result.immediate_stars_awarded:
            message += (
                " Начислено звёзд: "
                f"{result.immediate_stars_awarded}."
            )

        messages.success(
            request,
            message,
        )

    return redirect(
        "cheats:codes"

    )