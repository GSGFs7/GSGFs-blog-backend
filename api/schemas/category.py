"""Category and Tag schemas."""

from typing import List

from ninja.schema import Schema

from api.schemas import PaginationSchema, PostsCardSchema


class CategorySchema(Schema):
    id: int
    name: str


class CategoryResponseSchema(Schema):
    name: str
    pagination: PaginationSchema
    posts: List[PostsCardSchema]
