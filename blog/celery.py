import logging
import os

from celery import Celery
from celery.signals import worker_ready

logger = logging.getLogger(__name__)

# `celery -A blog worker -l info` needs this
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blog.settings")

app = Celery("blog")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.update(
    worker_concurrency=1,  # a worker is enough
)

# auto discover tasks
app.autodiscover_tasks()


@worker_ready.connect
def preload_ml_model(sender, **kwargs):
    """Preload ML model when worker starts to avoid first task timeout."""
    logger.info("Worker ready, preloading ML model...")
    try:
        # Import inside signal handler to avoid loading model when importing celery.py
        from api.ml_model import get_sentence_transformer_model

        model = get_sentence_transformer_model()
        logger.info(f"ML model preloaded successfully: {model}")
    except Exception as e:
        logger.warning(f"ML model preload failed: {e}")
