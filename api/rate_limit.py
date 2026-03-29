from functools import wraps
from typing import Callable

from django.core.cache import cache

from api.utils import is_async


def rate_limit(key_prefix: str, max_requests: int, window: int):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            # get ip
            client_ip: str = request.META.get("HTTP_X_FORWARDED_FOR")
            if client_ip:
                client_ip = client_ip.split(",")[0]
            else:
                client_ip = request.META.get("REMOTE_ADDR")

            cache_key = f"rate_limit:{key_prefix}:{client_ip}"
            await cache.aadd(cache_key, 0, timeout=window)
            current_requests = await cache.aincr(cache_key)
            if current_requests >= max_requests:
                return 429, {"message": "Too many request"}

            # run the raw func
            if is_async(func):
                return await func(request, *args, **kwargs)
            return func(request, *args, **kwargs)

        return wrapper

    return decorator
