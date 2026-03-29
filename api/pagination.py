# TODO: remove deprecated aliases,
#  read: https://docs.python.org/3.14/library/typing.html#deprecated-aliases
#  Zen of Python, line 13:
#  > There should be one-- and preferably only one --obvious way to do it.
from typing import Any, List, Type

from django.db.models import QuerySet
from django.http import HttpRequest
from ninja import Field, Schema
from ninja.pagination import AsyncPaginationBase
from pydantic import create_model

from api.schemas import PaginationSchema

__all__ = ["Pagination", "paginate_as"]


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
        total = self._items_count(queryset)

        return {
            self.items_attribute: queryset[offset : offset + pagination.size],
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

        # makesure this query be executed correctly (async/sync iterable)
        items = queryset[offset : offset + pagination.size]
        if hasattr(items, "__aiter__"):
            items = [p async for p in items]
        elif hasattr(items, "__iter__"):
            items = list(items)

        return {
            self.items_attribute: items,
            "pagination": {
                "page": pagination.page,
                "size": pagination.size,
                "total": total,
            },
        }

    @staticmethod
    def paginate_as(items_name: str, item_schema: Type[Any]) -> Type["Pagination"]:
        """
        Factory method to create a pagination class with a custom items field name.
        Useful to avoid creating multiple boilerplate subclasses for each router.
        """

        class CustomOutput(Schema):
            pagination: PaginationSchema

        # dynamically create a new pydantic model
        output_schema = create_model(
            f"PaginationOutput_{items_name}",
            **{items_name: (List[item_schema], ...)},
            __base__=CustomOutput,
        )

        # create a new class
        # noinspection PyTypeChecker
        return type(
            # class name
            f"Pagination_{items_name}",
            # father class
            (Pagination,),
            # class attributes
            {"items_attribute": items_name, "Output": output_schema},
        )


paginate_as = Pagination.paginate_as

# docs: https://django-ninja.dev/guides/response/pagination/
# source: https://github.com/vitalik/django-ninja/blob/master/ninja/pagination.py
