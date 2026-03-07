"""Gal (Visual Novel) schemas."""

import datetime
from typing import List, Optional

from ninja.schema import Schema

from .base import PaginationSchema


class GalSchema(Schema):
    id: int
    vndb_id: str
    title: Optional[str]
    title_cn: Optional[str]

    character_score: Optional[float]
    story_score: Optional[float]
    comprehensive_score: Optional[float]
    vndb_rating: Optional[float]

    created_at: datetime.datetime
    updated_at: datetime.datetime

    summary: Optional[str]
    review: Optional[str]
    review_html: Optional[str]

    cover_image: Optional[str]


class GalPaginationResponse(Schema):
    gals: List[GalSchema]
    pagination: PaginationSchema


class GalUpdateSchema(Schema):
    id: int
    vndb_id: str
    title: Optional[str]
    title_cn: Optional[str] = None

    character_score: Optional[float]
    story_score: Optional[float]
    comprehensive_score: Optional[float]
    vndb_rating: Optional[float]

    summary: Optional[str]
    review: Optional[str]

    cover_image: Optional[str]
