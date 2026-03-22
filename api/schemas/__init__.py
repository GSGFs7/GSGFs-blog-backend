"""API schemas package.

This package contains all Pydantic/Ninja schemas for the API.
Schemas are organized by domain for better maintainability.
"""

# Anime schemas
from .anime import (
    AnimeId,
    AnimeIds,
    AnimeSchema,
)

# Auth and Guest schemas
from .auth import (
    GuestLoginSchema,
    GuestSchema,
    LoginSchema,
    TokenSchema,
)

# Base schemas
from .base import (
    CategorySchema,
    ClientIdSchema,
    IdSchema,
    IdsSchema,
    MessageSchema,
    PaginationSchema,
    TagsSchema,
)

# Category schemas
from .category import CategoryResponseSchema

# Comment schemas
from .comment import (
    CommentIdsSchema,
    CommentPaginationResponse,
    CommentResponse,
    CommentSchema,
    NewCommentMetadataSchema,
    NewCommentSchema,
)

# Gal (Visual Novel) schemas
from .gal import (
    GalPaginationResponse,
    GalSchema,
    GalUpdateSchema,
)

# Image
from .image import ImageUploadRequestSchema, ImageUploadResponseSchema

# Post schemas
from .post import (
    PostCardsSchema,
    PostCardsWithSimilaritySchema,
    PostCardWithSimilarity,
    PostRenderedSchema,
    PostsCardSchema,
    PostsSchema,
)

# Sitemap schemas
from .sitemap import PostIdsForSitemap, PostSitemapSchema

# System and health check schemas
from .system import (
    ApiStatusSchema,
    DatabaseStatusSchema,
    SystemInfoSchema,
)

__all__ = [
    # Base
    "PaginationSchema",
    "MessageSchema",
    "IdSchema",
    "IdsSchema",
    # Auth
    "ClientIdSchema",
    # Category & Tags
    "CategorySchema",
    "TagsSchema",
    # Comments
    "CommentSchema",
    "CommentPaginationResponse",
    "CommentResponse",
    "CommentIdsSchema",
    "NewCommentMetadataSchema",
    "NewCommentSchema",
    # Posts
    "PostsSchema",
    "PostsCardSchema",
    "PostCardsSchema",
    "CategoryResponseSchema",
    "PostRenderedSchema",
    "PostCardWithSimilarity",
    "PostCardsWithSimilaritySchema",
    # Auth
    "LoginSchema",
    "TokenSchema",
    "GuestSchema",
    "GuestLoginSchema",
    # Sitemap
    "PostSitemapSchema",
    "PostIdsForSitemap",
    # Gal
    "GalSchema",
    "GalPaginationResponse",
    "GalUpdateSchema",
    # Image
    "ImageUploadRequestSchema",
    "ImageUploadResponseSchema",
    # Anime
    "AnimeId",
    "AnimeIds",
    "AnimeSchema",
    # System
    "SystemInfoSchema",
    "DatabaseStatusSchema",
    "ApiStatusSchema",
]
