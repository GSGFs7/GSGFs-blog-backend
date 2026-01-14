from functools import lru_cache

from django.conf import settings
from sentence_transformers import SentenceTransformer


# Repeated loading of the model is too time-consuming
# We keep it always in memory
@lru_cache(1)
def get_sentence_transformer_model() -> SentenceTransformer:
    model = SentenceTransformer(
        settings.MODEL_NAME,
        cache_folder=settings.SENTENCE_TRANSFORMERS_HOME,
        local_files_only=True,
    )

    return model
