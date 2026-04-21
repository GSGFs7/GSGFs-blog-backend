from django.conf import settings
from django.urls import path

from . import views

# frontend not available now!
urlpatterns = (
    [
        path("", views.index, name="index"),
        path("test", views.test, name="test"),
        path("blog", views.blog, name="blog"),
        path("blog/<int:post_id>", views.blog_post, name="blog post"),
        path("about", views.about, name="about"),
    ]
    if settings.DEBUG
    else []
)
