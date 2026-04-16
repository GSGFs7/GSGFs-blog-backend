from django.conf import settings
from django.urls import path

from . import views

# TODO: frontend not available now!
urlpatterns = (
    [
        path("", views.index, name="index"),
    ]
    if settings.DEBUG
    else []
)
