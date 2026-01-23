"""
use `jikan.py`, not this file
"""

from typing import List, Optional

import requests
from pydantic import BaseModel


class AnimeTitle(BaseModel):
    romaji: str
    english: str
    native: str


class AnimeCoverImage(BaseModel):
    extraLarge: str
    color: Optional[str]


class AnimeEndDate(BaseModel):
    year: int
    month: int


class AnimeMedia(BaseModel):
    id: int
    title: AnimeTitle
    coverImage: AnimeCoverImage
    description: str
    isAdult: bool
    endDate: AnimeEndDate


class AnimeData(BaseModel):
    # if have some error it will be None
    Media: Optional[AnimeMedia] = None


class AnimeError(BaseModel):
    message: str
    status: int


class AnimeResponse(BaseModel):
    data: AnimeData
    errors: Optional[List[AnimeError]]


def query_anime(anime_id: int):
    query = """
    query ($id: Int) {
        Media (id: $id, type: ANIME) { 
            id
            title {
                romaji
                english
                native
            }
            coverImage {
                extraLarge
                color
            }
            description
            isAdult
            endDate {
                year
                month
            }
        }
    }
    """
    url = "https://graphql.anilist.co"
    variables = {"id": anime_id}

    response = requests.post(url, json={"query": query, "variables": variables})
    response.raise_for_status()
    # print(response.json())

    anime_response = AnimeResponse.model_validate(response.json())
    return anime_response.data.Media


if __name__ == "__main__":
    try:
        anime = query_anime(57433)

        if anime is None:
            pass
        else:
            print(anime.title.native)
            print(anime.description)
    except Exception as e:
        print(e)
