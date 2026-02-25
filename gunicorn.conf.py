# gunicorn.conf.py

import os


def is_k8s_env() -> bool:
    return os.environ.get("K8S_ENV", "False").lower() in ("1", "true", "yes")


# Port
bind = "0.0.0.0:8000"

# Workers and threads
workers = 1 if is_k8s_env() else 3
threads = 1
worker_class = "sync"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = (
    "debug" if (os.environ.get("DEBUG", "false") in ("1", "true", "yes")) else "info"
)
capture_output = True

daemon = False
