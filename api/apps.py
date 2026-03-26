from django.apps import AppConfig

from api.exiftool import ExifTool


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self) -> None:
        # Import signals to make sure they are registered
        import api.signals  # noqa: F401

        # run exiftool process
        if ExifTool.is_available():
            ExifTool()

        return super().ready()
