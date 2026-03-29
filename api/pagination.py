from typing import Any, List

from django.db.models import QuerySet
from django.http import HttpRequest
from ninja import Field, Schema
from ninja.pagination import AsyncPaginationBase

from api.schemas import PaginationSchema


class Pagination(AsyncPaginationBase):
    # Query Params
    class Input(Schema):
        page: int = Field(1, ge=1)
        size: int = Field(10, ge=1, le=100)

    class Output(Schema):
        result: List[Any]  # in API endpoint definition, MUST use List[...]
        pagination: PaginationSchema

    # tall pagination which is result field
    items_attribute: str = "result"

    def paginate_queryset(
        self,
        queryset: QuerySet,
        pagination: Input,
        request: HttpRequest,
        **params: Any,
    ) -> dict:
        offset = (pagination.page - 1) * pagination.size
        total = self._aitems_count(queryset)

        return {
            "result": queryset[offset : offset + pagination.size],
            "pagination": {
                "page": pagination.page,
                "size": pagination.size,
                "total": total,
            },
        }

    async def apaginate_queryset(
        self,
        queryset: QuerySet,
        pagination: Input,
        request: HttpRequest,
        **params: Any,
    ) -> dict:
        # calculate offset
        offset = (pagination.page - 1) * pagination.size
        total = await self._aitems_count(queryset)

        return {
            "result": queryset[offset : offset + pagination.size],
            "pagination": {
                "page": pagination.page,
                "size": pagination.size,
                "total": total,
            },
        }


# docs: https://django-ninja.dev/guides/response/pagination/
# source: https://github.com/vitalik/django-ninja/blob/master/ninja/pagination.py
