import os
from django.conf import settings
from sentence_transformers import SentenceTransformer

# Repeated loading of the model is too time-consuming
# We keep it always in memory
model = None


def get_sentence_transformer_model() -> SentenceTransformer:
    global model

    if model is None:
        model = SentenceTransformer(
            settings.MODEL_NAME,
            cache_folder=settings.SENTENCE_TRANSFORMERS_HOME,
            # token=os.environ.get("HUGGINGFACE_HUB_TOKEN"),
            local_files_only=True,
        )

    return model
