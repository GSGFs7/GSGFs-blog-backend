from functools import wraps
from django.core.cache import cache
from typing import Callable


def rate_limit(key_prefix: str, max_requests: int, window: int):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            client_ip: str = request.META.get("HTTP_X_FORWARDED_FOR")
            if client_ip:
                client_ip = client_ip.split(",")[0]
            else:
                client_ip = request.META.get("REMOTE_ADDR")

            cache_key = f"{key_prefix}:{client_ip}"
            current_requests = cache.get(cache_key, 0)
            if current_requests >= max_requests:
                return 429, {"message": "Too many request"}

            cache.set(cache_key, current_requests + 1, window)

            # run the raw func
            return func(request, *args, **kwargs)

        return wrapper

    return decorator
