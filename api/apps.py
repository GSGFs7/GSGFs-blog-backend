import sys

from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self) -> None:
        # Import signals to make sure they are registered
        import api.signals  # noqa: F401

        # if don't need init
        if "manage.py" in sys.argv:
            if not any(arg in sys.argv for arg in ["runserver", "shell"]):
                return None

        # if SyncExifTool.is_available():
        #     SyncExifTool()

        return None
