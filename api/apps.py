from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self) -> None:
        # Import signals to make sure they are registered
        import api.signals

        from . import ml_model

        # Preload machine learning model
        # This operation will slow down `./manage.py makemigrations && ./manage.py migrate`
        # Lazy load is enough
        # if not settings.DEBUG:
        #     ml_model.get_sentence_transformer_model()

        return super().ready()
