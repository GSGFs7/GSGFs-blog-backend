from django.http import HttpRequest
from django.shortcuts import render


# Create your views here.
def index(request: HttpRequest):
    return render(request, "web/pages/index.html")


def test(request: HttpRequest):
    return render(request, "web/pages/test.html")


def blog(request: HttpRequest):
    return render(request, "web/pages/blog.html")


def about(request: HttpRequest):
    return render(request, "web/pages/about.html")
