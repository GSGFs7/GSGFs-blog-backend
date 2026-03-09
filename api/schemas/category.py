"""Category and Tag schemas."""

from typing import List

from ninja.schema import Schema

from .base import PaginationSchema
from .post import PostsCardSchema


class CategoryResponseSchema(Schema):
    name: str
    pagination: PaginationSchema
    posts: List[PostsCardSchema]
