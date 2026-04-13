import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from media_service.models import ImageResource
from media_service.tasks import process_image

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ImageResource)
def trigger_image_processing(sender, instance: ImageResource, created, **kwargs):
    """
    Trigger image processing (compression, format conversion) after upload.

    sync function, it will running in the thead pool
    """
    if (
        created
        or not instance.webp_file
        or not instance.avif_file
        or not instance.thumbnail
    ):
        try:

            def task():
                process_image.delay(instance.pk)
                logger.info(f"Triggered image processing for Image ID {instance.pk}")

            transaction.on_commit(task)
        except Exception as e:
            logger.error(
                f"Failed to trigger image processing for Image ID {instance.pk}: {e}"
            )
