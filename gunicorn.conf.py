# gunicorn.conf.py

import multiprocessing

# 端口
bind = "0.0.0.0:8000"

# 进程和线程
workers = multiprocessing.cpu_count()
threads = 2
worker_class = "sync"

# 日志
accesslog = "-"
errorlog = "-"
loglevel = "info"
capture_output = True

daemon = False
