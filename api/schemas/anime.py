"""Anime schemas."""

from typing import List, Optional

from ninja.schema import Schema

from .base import PaginationSchema


class AnimeId(Schema):
    id: int
    name: str
    score: Optional[float]
    cover_image: str


class AnimeIds(Schema):
    ids: List[AnimeId]
    pagination: PaginationSchema


class AnimeSchema(Schema):
    id: int
    mal_id: int
    name: str
    name_cn: Optional[str]
    year: Optional[int]
    synopsis: Optional[str]
    cover_image: Optional[str]
    rating: str

    score: Optional[float]
    review: Optional[str]
