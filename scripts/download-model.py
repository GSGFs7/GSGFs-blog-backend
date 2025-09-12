#!/usr/bin/env python


import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


def is_docker_env() -> bool:
    return os.environ.get("DOCKER_ENV", "false").lower() in ("1", "true", "yes")


if __name__ == "__main__":
    load_dotenv()

    MODEL_NAME = os.environ.get("MODEL_NAME")
    if MODEL_NAME is None:
        raise ValueError("MODEL_NAME environment variable is not set.")

    SENTENCE_TRANSFORMERS_HOME = os.environ.get("SENTENCE_TRANSFORMERS_HOME")
    if SENTENCE_TRANSFORMERS_HOME is None:
        raise ValueError("SENTENCE_TRANSFORMERS_HOME environment variable is not set.")

    HUGGINGFACE_HUB_TOKEN = os.environ.get("HUGGINGFACE_HUB_TOKEN")
    if HUGGINGFACE_HUB_TOKEN is None:
        raise ValueError("HUGGINGFACE_HUB_TOKEN environment variable is not set.")

    res = SentenceTransformer(
        MODEL_NAME,
        cache_folder=SENTENCE_TRANSFORMERS_HOME,
        token=HUGGINGFACE_HUB_TOKEN,
    )
