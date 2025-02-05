import datetime
from typing import List, Optional

from ninja.schema import Schema


class CategorySchema(Schema):
    id: int
    name: str


class TagsSchema(Schema):
    id: int
    name: str


class PostsSchema(Schema):
    id: int
    category: Optional[CategorySchema] = None
    content: str
    cover_image: Optional[str]
    created_at: datetime.datetime
    header_image: Optional[str]
    meta_description: str
    order: int
    slug: str
    status: str
    tags: Optional[List[TagsSchema]] = None
    title: str
    update_at: datetime.datetime
    view_count: int


class PostsCardSchema(Schema):
    id: int
    category: Optional[CategorySchema]
    cover_image: Optional[str]
    created_at: datetime.datetime
    meta_description: str
    slug: str
    tags: Optional[List[TagsSchema]]
    title: str
    update_at: datetime.datetime


class PaginationSchema(Schema):
    page: int
    size: int
    total: int


class PostsCardsSchema(Schema):
    pagination: PaginationSchema
    posts: List[PostsCardSchema]


# 跟正常查询一样的
class CategoryResponseSchema(Schema):
    name: str
    pagination: PaginationSchema
    posts: List[PostsCardSchema]


class MessageSchema(Schema):
    message: str


class renderSchema(Schema):
    id: int
    author: Optional[str] = None
    category: Optional[str] = None
    content_html: Optional[str] = None
    cover_image: Optional[str] = None
    header_image: Optional[str] = None
    meta_description: Optional[str] = None
    slug: Optional[str] = None
    tags: Optional[List[str]] = None
    title: Optional[str] = None


class LoginSchema(Schema):
    email: str
    provider: str
    username: str
    password: str


class TokenSchema(Schema):
    access_token: str
    token_type: str = "bearer"
