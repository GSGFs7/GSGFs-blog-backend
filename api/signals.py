from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Page, Post
from .utils import extract_keywords


@receiver(pre_save, sender=Post)
@receiver(pre_save, sender=Page)
def add_keywords(sender, instance, **kwargs):
    if not instance.keywords:
        instance.keywords = extract_keywords(instance.content)
