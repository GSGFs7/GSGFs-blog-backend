import os
from typing import List, Literal, Optional, TypedDict

import requests


class Title(TypedDict):
    title: str
    lang: str


class Image(TypedDict):
    url: str


class VNItem(TypedDict):
    id: str
    alttile: Optional[str]
    rating: float
    title: str
    titles: List[Title]
    image: Image


class VNDBResponse(TypedDict):
    results: List[VNItem]
    more: bool


def query_vn(id: str) -> VNDBResponse:
    fields = [
        "title",
        "alttitle",
        "titles.lang",
        "titles.title",
        "image.url",
        "rating",
    ]

    res = requests.post(
        "https://api.vndb.org/kana/vn",
        headers={
            "Content-Type": "application/json",
            "User-Agent": f"Django (+https://{os.getenv('SERVER_NAME', 'Unknown')})",
        },
        json={
            "filters": ["id", "=", id],
            "fields": ", ".join(fields),
        },
    )

    return res.json()
