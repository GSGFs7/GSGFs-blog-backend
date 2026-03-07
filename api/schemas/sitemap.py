"""Sitemap schemas."""

import datetime
from typing import List

from ninja.schema import Schema
from pydantic import Field, RootModel


class PostSitemapSchema(Schema):
    id: int
    slug: str
    updated_at: datetime.datetime = Field(alias="content_update_at")

    class Config:
        populate_by_name = True


class PostIdsForSitemap(RootModel):
    root: List[PostSitemapSchema]

    class Config:
        from_attributes = True
