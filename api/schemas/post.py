"""Post schemas."""

import datetime
from typing import List, Optional

from ninja.schema import Schema

from .base import CategorySchema, PaginationSchema, TagsSchema


class PostSchema(Schema):
    id: int
    category: Optional[CategorySchema] = None
    content: str
    content_html: Optional[str]
    cover_image: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    content_update_at: datetime.datetime
    header_image: Optional[str]
    meta_description: str
    keywords: Optional[str] = None
    order: int
    slug: str
    status: str
    tags: Optional[List[TagsSchema]] = None
    title: str
    view_count: int


class PostCardSchema(Schema):
    id: int
    title: str
    slug: str
    meta_description: str
    cover_image: Optional[str]
    category: Optional[CategorySchema]
    tags: Optional[List[TagsSchema]]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    content_update_at: datetime.datetime


class PostCardsSchema(Schema):
    pagination: PaginationSchema
    posts: List[PostCardSchema]


class PostRenderedSchema(Schema):
    id: int
    category: Optional[str] = None
    content_html: Optional[str] = None
    cover_image: Optional[str] = None
    header_image: Optional[str] = None
    meta_description: Optional[str] = None
    slug: Optional[str] = None
    tags: Optional[List[str]] = None
    title: Optional[str] = None


class PostCardWithSimilarity(Schema):
    post: PostCardSchema
    similarity: float


class PostCardsWithSimilaritySchema(Schema):
    posts_with_similarity: List[PostCardWithSimilarity]
    pagination: PaginationSchema
