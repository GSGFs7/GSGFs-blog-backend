import platform
import time
from datetime import datetime
from typing import Any, Dict, List

import psutil
from django.conf import settings
from django.db import connections
from ninja import Router

from ..auth import TimeBaseAuth
from ..schemas import (
    ApiStatusSchema,
    DatabaseStatusSchema,
    MessageSchema,
    SystemInfoSchema,
)

router = Router()


@router.get("/", response=MessageSchema)
def heath_status(request):
    return {"message": "OK"}


@router.get("/status", response=ApiStatusSchema, auth=TimeBaseAuth())
def api_status(request):
    system_info = get_system_info()
    databases_status = check_database_connections()
    dependencies = check_dependencies()

    return {
        "status": "online",
        "version": get_version(),
        "environment": get_environment(),
        "timestamp": datetime.now().isoformat(),
        "databases": databases_status,
        "system": system_info,
        "dependencies": dependencies,
    }


def get_system_info() -> SystemInfoSchema:
    """collection system information"""

    return SystemInfoSchema(
        hostname=platform.node(),
        platform=f"{platform.system()} {platform.release()}",
        cpu_usage=psutil.cpu_percent(interval=0.1),
        memory_usage=psutil.virtual_memory().percent,
        disk_usage=psutil.disk_usage("/").percent,
        uptime=time.time() - psutil.boot_time(),  # seconds
    )


def check_database_connections() -> List[DatabaseStatusSchema]:
    """check databases connection status"""

    result = []

    for connection_name in connections:
        connection = connections[connection_name]
        start_time = time.time()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            status = "connected"
        except Exception as e:
            status = f"error: {str(e)}"

        response_time = time.time() - start_time
        result.append(
            {
                "name": connection_name,
                "status": status,
                "response_time": response_time,
            }
        )
    return result


def check_dependencies() -> Dict[str, Any]:
    dependencies = {}

    try:
        from django.core.cache import cache

        cache_key = "health_check"
        cache_value = time.time()
        cache.set(cache_key, cache_value, 10)
        retrieved = cache.get(cache_key)

        if retrieved == cache_value:
            dependencies["cache"] = "connected"
            dependencies["cache_response_time"] = time.time() - float(retrieved)
        else:
            dependencies["cache"] = "error: value mismatch"
    except Exception as e:
        dependencies["cache"] = f"error:{str(e)}"

    return dependencies


def get_environment() -> str:
    debug_mode = getattr(settings, "DEBUG", True)
    return "development" if debug_mode else "production"


def get_version() -> str:
    """get the version of API"""

    version = getattr(settings, "API_VERSION", "unknown")

    return version
