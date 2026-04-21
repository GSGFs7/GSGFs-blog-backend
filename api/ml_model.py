from functools import lru_cache

from django.conf import settings


@lru_cache(1)
def get_sentence_transformer_model():
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(
        settings.MODEL_NAME,
        cache_folder=settings.SENTENCE_TRANSFORMERS_HOME,
        local_files_only=True,
    )

    return model
