"""System and health check schemas."""

from typing import Any, Dict, List

from ninja.schema import Schema


class SystemInfoSchema(Schema):
    hostname: str
    platform: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    uptime: float


class DatabaseStatusSchema(Schema):
    name: str
    status: str
    response_time: float


class ApiStatusSchema(Schema):
    status: str
    version: str
    environment: str
    timestamp: str
    databases: List[DatabaseStatusSchema]
    system: SystemInfoSchema
    dependencies: Dict[str, Any]
