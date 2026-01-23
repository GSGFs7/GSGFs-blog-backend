from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self) -> None:
        # Import signals to make sure they are registered
        import api.signals  # noqa: F401

        return super().ready()
