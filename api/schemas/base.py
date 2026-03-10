"""Base schemas for API responses."""

from typing import List

from ninja.schema import Schema


class PaginationSchema(Schema):
    page: int
    size: int
    total: int


class MessageSchema(Schema):
    message: str


class IdSchema(Schema):
    id: int


class IdsSchema(Schema):
    ids: List[int]


class CategorySchema(Schema):
    id: int
    name: str


class TagsSchema(Schema):
    id: int
    name: str
