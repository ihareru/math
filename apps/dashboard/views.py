from django.shortcuts import render


def home(request):
    return render(
        request,
        "dashboard/home.html",
    )


from django.shortcuts import render

# Create your views here.
