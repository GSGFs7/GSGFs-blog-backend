import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blog.settings")

app = Celery("blog")

app.config_from_object("django.conf:settings", namespace="CELERY")

# auto discover tasks
app.autodiscover_tasks()
