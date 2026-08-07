from django.core.paginator import Paginator
from django.shortcuts import render

from .services.rating import (
    build_public_rating,
    find_user_rating_row,
    get_public_rating_summary,
)


RATING_PAGE_SIZE = 25


def home(request):
    rating_rows = build_public_rating()

    paginator = Paginator(
        rating_rows,
        RATING_PAGE_SIZE,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    current_user_rating = find_user_rating_row(
        rating_rows=rating_rows,
        user=request.user,
    )

    rating_summary = get_public_rating_summary()

    return render(
        request,
        "dashboard/home.html",
        {
            "page_obj": page_obj,
            "rating_summary": rating_summary,
            "current_user_rating": (
                current_user_rating
            ),
        },
    )