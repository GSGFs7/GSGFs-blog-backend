#!/usr/bin/env python


import logging
import os

from dotenv import load_dotenv
from filelock import FileLock
from huggingface_hub import snapshot_download
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
    GGUF_MODEL_NAME = os.environ.get("GGUF_MODEL_NAME")

    if MODEL_NAME is None and GGUF_MODEL_NAME is None:
        raise ValueError(
            "Neither MODEL_NAME nor GGUF_MODEL_NAME environment variable is set."
        )

    SENTENCE_TRANSFORMERS_HOME = os.environ.get("SENTENCE_TRANSFORMERS_HOME")
    if SENTENCE_TRANSFORMERS_HOME is None:
        raise ValueError("SENTENCE_TRANSFORMERS_HOME environment variable is not set.")

    HUGGINGFACE_HUB_TOKEN = os.environ.get("HUGGINGFACE_HUB_TOKEN")
    if HUGGINGFACE_HUB_TOKEN is None:
        raise ValueError("HUGGINGFACE_HUB_TOKEN environment variable is not set.")
    HUGGINGFACE_HUB_TOKEN = HUGGINGFACE_HUB_TOKEN.strip()

    # Create model cache directory if it doesn't exist
    os.makedirs(SENTENCE_TRANSFORMERS_HOME, exist_ok=True)

    # Use a lock file to prevent multiple pods from downloading at the same time
    # Combine model names for the lock file name
    lock_id = f"{MODEL_NAME or ''}_{GGUF_MODEL_NAME or ''}".replace("/", "_")
    lock_file = os.path.join(SENTENCE_TRANSFORMERS_HOME, f"{lock_id}.lock")
    lock = FileLock(lock_file)

    logger.info("Acquiring lock for model downloading...")
    with lock:
        if MODEL_NAME:
            logger.info(f"Lock acquired. Starting download/load of {MODEL_NAME}")
            SentenceTransformer(
                MODEL_NAME,
                cache_folder=SENTENCE_TRANSFORMERS_HOME,
                token=HUGGINGFACE_HUB_TOKEN,
            )
            logger.info(f"Model {MODEL_NAME} is ready.")

        if GGUF_MODEL_NAME:
            logger.info(f"Starting download of GGUF model: {GGUF_MODEL_NAME}")
            local_dir = os.path.join(
                SENTENCE_TRANSFORMERS_HOME, GGUF_MODEL_NAME.replace("/", "--")
            )
            snapshot_download(
                repo_id=GGUF_MODEL_NAME,
                local_dir=local_dir,
                token=HUGGINGFACE_HUB_TOKEN,
            )
            logger.info(f"GGUF Model {GGUF_MODEL_NAME} is ready at {local_dir}")
