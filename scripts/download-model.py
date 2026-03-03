#!/usr/bin/env python


import logging
import os

from dotenv import load_dotenv
from filelock import FileLock
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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

    # Create model cache directory if it doesn't exist
    os.makedirs(SENTENCE_TRANSFORMERS_HOME, exist_ok=True)

    # Use a lock file to prevent multiple pods from downloading at the same time
    lock_file = os.path.join(
        SENTENCE_TRANSFORMERS_HOME, f"{MODEL_NAME.replace('/', '_')}.lock"
    )
    lock = FileLock(lock_file)

    logger.info(f"Acquiring lock for model: {MODEL_NAME}")
    with lock:
        logger.info(f"Lock acquired. Starting download/load of {MODEL_NAME}")
        SentenceTransformer(
            MODEL_NAME,
            cache_folder=SENTENCE_TRANSFORMERS_HOME,
            token=HUGGINGFACE_HUB_TOKEN,
        )
        logger.info(f"Model {MODEL_NAME} is ready.")
