from importlib import import_module

from django.apps import AppConfig


class MediaServiceConfig(AppConfig):
    name = "media_service"

    def ready(self):
        import_module("media_service.signals")
