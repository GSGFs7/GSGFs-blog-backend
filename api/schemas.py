import datetime
from typing import List, Optional

from ninja.schema import Schema
from pydantic import RootModel


class CategorySchema(Schema):
    id: int
    name: str


class TagsSchema(Schema):
    id: int
    name: str


class CommentSchema(Schema):
    id: int
    content: str
    post_id: int
    guest_id: int
    guest_name: str
    created_at: datetime.datetime
    update_at: datetime.datetime
    avatar: str

    # 从关联的 guest 获取name
    @staticmethod
    def resolve_guest_name(obj):
        return obj.guest.name

    @staticmethod
    def resolve_avatar(obj):
        return obj.guest.avatar


class CommentIdsSchema(Schema):
    ids: List[int]


class PostsSchema(Schema):
    id: int
    category: Optional[CategorySchema] = None
    content: str
    cover_image: Optional[str]
    created_at: datetime.datetime
    update_at: datetime.datetime
    header_image: Optional[str]
    meta_description: str
    order: int
    slug: str
    status: str
    tags: Optional[List[TagsSchema]] = None
    title: str
    view_count: int
    # comment_id: Optional[List[int]] = None  # 单独获取


# 省略版本
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


class RenderSchema(Schema):
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


class GuestSchema(Schema):
    id: int
    name: str
    provider: str
    provider_id: int
    unique_id: str
    email: Optional[str]


class GuestLoginSchema(Schema):
    name: str
    provider: str
    provider_id: int
    avatar_url: str


class IdSchema(Schema):
    id: int


class NewCommentMetadataSchema(Schema):
    user_agent: str
    platform: str
    browser: str
    browser_version: str
    OS: str


class NewCommentSchema(Schema):
    unique_id: str
    content: str
    post_id: int
    metadata: Optional[NewCommentMetadataSchema]


class PostSitemapSchema(Schema):
    id: int
    slug: str
    update_at: datetime.datetime


class PostIdsForSitemap(RootModel):
    root: List[PostSitemapSchema]

    class Config:
        from_attributes = True
