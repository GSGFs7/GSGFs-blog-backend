import os

from celery import Celery

# `celery -A blog worker -l info` needs this
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blog.settings")

app = Celery("blog")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.update(
    worker_concurrency=1,  # a worker is enough
)

# auto discover tasks
app.autodiscover_tasks()
