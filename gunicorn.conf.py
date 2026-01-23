# gunicorn.conf.py

import os

# 端口
bind = "0.0.0.0:8000"

# 进程和线程
workers = 3
threads = 2
worker_class = "sync"

# 日志
accesslog = "-"
errorlog = "-"
loglevel = (
    "debug" if (os.environ.get("DEBUG", "false") in ("1", "true", "yes")) else "info"
)
capture_output = True

daemon = False
