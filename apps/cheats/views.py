from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
)
from django.contrib.admin.views.decorators import (
    staff_member_required,
)
from django.shortcuts import redirect, render
from django.views.decorators.http import (
    require_POST,
)
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from apps.analytics.services.client import (
    get_client_ip,
)

from .forms import (
    CheatActivationForm,
    ActivationFilterForm,
    CheatCodeAdminForm,
    CheatRewardFormSet,
)
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
from .services.admin_dashboard import (
    get_cheat_admin_statistics,
    get_popular_cheat_codes,
)
from .models import UserCheat, CheatCode


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

@staff_member_required
def admin_dashboard(request):
    context = {
        **get_cheat_admin_statistics(),
        "popular_codes": (
            get_popular_cheat_codes(
                limit=10,
            )
        ),
        "recent_activations": (
            UserCheat.objects
            .select_related(
                "user",
                "cheat",
            )
            .order_by("-activated_at")[:10]
        ),
    }

    return render(
        request,
        "cheats/admin/dashboard.html",
        context,
    )


@staff_member_required
def admin_code_list(request):
    search_query = (
        request.GET.get("search", "")
        .strip()
    )

    status = request.GET.get(
        "status",
        "",
    )

    codes = (
        CheatCode.objects
        .prefetch_related("rewards")
        .annotate(
            actual_activation_count=Count(
                "user_activations"
            ),
            unique_user_count=Count(
                "user_activations__user",
                distinct=True,
            ),
        )
        .order_by("name")
    )

    if search_query:
        codes = codes.filter(
            Q(name__icontains=search_query)
            | Q(code__icontains=search_query)
            | Q(
                description__icontains=search_query
            )
        )

    if status == "enabled":
        codes = codes.filter(
            is_active=True,
        )

    elif status == "disabled":
        codes = codes.filter(
            is_active=False,
        )

    paginator = Paginator(
        codes,
        25,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "cheats/admin/code_list.html",
        {
            "page_obj": page_obj,
            "search_query": search_query,
            "status": status,
        },
    )

@staff_member_required
@transaction.atomic
def admin_code_create(request):
    cheat = CheatCode()

    if request.method == "POST":
        form = CheatCodeAdminForm(
            request.POST,
            instance=cheat,
        )

        reward_formset = CheatRewardFormSet(
            request.POST,
            instance=cheat,
            prefix="rewards",
        )

        if (
            form.is_valid()
            and reward_formset.is_valid()
        ):
            cheat = form.save()

            reward_formset.instance = cheat
            reward_formset.save()

            messages.success(
                request,
                (
                    f"Чит-код {cheat.code} "
                    "успешно создан."
                ),
            )

            return redirect(
                "cheats:admin_code_list"
            )
    else:
        form = CheatCodeAdminForm(
            instance=cheat,
        )

        reward_formset = CheatRewardFormSet(
            instance=cheat,
            prefix="rewards",
        )

    return render(
        request,
        "cheats/admin/code_form.html",
        {
            "form": form,
            "reward_formset": reward_formset,
            "page_title": "Создание чит-кода",
            "submit_label": "Создать код",
            "cheat": None,
        },
    )

@staff_member_required
@transaction.atomic
def admin_code_edit(
    request,
    code_id,
):
    cheat = get_object_or_404(
        CheatCode,
        pk=code_id,
    )

    if request.method == "POST":
        form = CheatCodeAdminForm(
            request.POST,
            instance=cheat,
        )

        reward_formset = CheatRewardFormSet(
            request.POST,
            instance=cheat,
            prefix="rewards",
        )

        if (
            form.is_valid()
            and reward_formset.is_valid()
        ):
            cheat = form.save()
            reward_formset.save()

            messages.success(
                request,
                (
                    f"Чит-код {cheat.code} "
                    "сохранён."
                ),
            )

            return redirect(
                "cheats:admin_code_edit",
                code_id=cheat.pk,
            )
    else:
        form = CheatCodeAdminForm(
            instance=cheat,
        )

        reward_formset = CheatRewardFormSet(
            instance=cheat,
            prefix="rewards",
        )

    return render(
        request,
        "cheats/admin/code_form.html",
        {
            "form": form,
            "reward_formset": reward_formset,
            "page_title": (
                f"Редактирование {cheat.code}"
            ),
            "submit_label": "Сохранить",
            "cheat": cheat,
        },
    )

@staff_member_required
@require_POST
def admin_code_toggle(
    request,
    code_id,
):
    cheat = get_object_or_404(
        CheatCode,
        pk=code_id,
    )

    cheat.is_active = not cheat.is_active

    cheat.save(
        update_fields=[
            "is_active",
            "updated_at",
        ]
    )

    if cheat.is_active:
        message = (
            f"Код {cheat.code} включён."
        )
    else:
        message = (
            f"Код {cheat.code} отключён."
        )

    messages.success(
        request,
        message,
    )

    return redirect(
        request.POST.get("next")
        or "cheats:admin_code_list"
    )

@staff_member_required
def admin_activation_list(request):
    form = ActivationFilterForm(
        request.GET or None
    )

    activations = (
        UserCheat.objects
        .select_related(
            "user",
            "cheat",
        )
        .order_by("-activated_at")
    )

    if form.is_valid():
        search_query = (
            form.cleaned_data["search"]
            .strip()
        )

        status = form.cleaned_data[
            "status"
        ]

        if search_query:
            activations = activations.filter(
                Q(
                    user__display_name__icontains=(
                        search_query
                    )
                )
                | Q(
                    user__email__icontains=(
                        search_query
                    )
                )
                | Q(
                    cheat__code__icontains=(
                        search_query
                    )
                )
                | Q(
                    cheat__name__icontains=(
                        search_query
                    )
                )
            )

        now = timezone.now()

        if status == "active":
            activations = (
                activations
                .filter(is_active=True)
                .filter(
                    Q(expires_at__isnull=True)
                    | Q(expires_at__gt=now)
                )
            )

        elif status == "expired":
            activations = activations.filter(
                is_active=True,
                expires_at__isnull=False,
                expires_at__lte=now,
            )

        elif status == "disabled":
            activations = activations.filter(
                is_active=False,
            )

    paginator = Paginator(
        activations,
        30,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "cheats/admin/activation_list.html",
        {
            "form": form,
            "page_obj": page_obj,
        },
    )

@staff_member_required
def admin_code_activations(
    request,
    code_id,
):
    cheat = get_object_or_404(
        CheatCode,
        pk=code_id,
    )

    activations = (
        UserCheat.objects
        .filter(cheat=cheat)
        .select_related("user")
        .order_by("-activated_at")
    )

    paginator = Paginator(
        activations,
        30,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "cheats/admin/code_activations.html",
        {
            "cheat": cheat,
            "page_obj": page_obj,
        },
    )

@staff_member_required
@require_POST
def admin_activation_disable(
    request,
    activation_id,
):
    activation = get_object_or_404(
        UserCheat.objects.select_related(
            "user",
            "cheat",
        ),
        pk=activation_id,
    )

    if activation.is_active:
        activation.is_active = False

        activation.save(
            update_fields=[
                "is_active",
            ]
        )

        messages.success(
            request,
            (
                f"Бонус {activation.cheat.code} "
                "для пользователя "
                f"{activation.user.display_name} "
                "отключён."
            ),
        )
    else:
        messages.info(
            request,
            "Эта активация уже отключена.",
        )

    return redirect(
        request.POST.get("next")
        or "cheats:admin_activation_list"
    )

