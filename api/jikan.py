from typing import List, Literal, Optional

import requests
from pydantic import BaseModel


class AnimeImageUrls(BaseModel):
    image_url: str
    small_image_url: str
    large_image_url: str


class AnimeImage(BaseModel):
    jpg: AnimeImageUrls
    webp: AnimeImageUrls


class AnimeTitles(BaseModel):
    type: str
    title: str


# only i need, not all
class AnimeData(BaseModel):
    mal_id: int
    url: str
    images: AnimeImage
    approved: bool  # Whether the entry is pending approval on MAL or not
    titles: List[AnimeTitles]
    rating: Literal[
        "G - All Ages",
        "PG - Children",
        "PG-13 - Teens 13 or older",
        "R - 17+ (violence & profanity)",
        "R+ - Mild Nudity",
        "Rx - Hentai",
    ]  # https://en.wikipedia.org/wiki/Motion_Picture_Association_film_rating_system
    episodes: Optional[int] = None  # Episode count
    score: Optional[float] = None
    synopsis: Optional[str] = None
    year: Optional[int] = None
    # title: str  # Deprecated
    # title_english: Optional[str] = None  # Deprecated
    # title_japanese: Optional[str] = None  # Deprecated


class AnimeResponse(BaseModel):
    data: AnimeData


def query_anime(id: int) -> AnimeData:
    """
    Fetches anime information from the Jikan API using the provided MyAnimeList (MAL) anime ID.

    Args:
        id (int): The MAL ID of the anime to query.

    Returns:
        AnimeData: An instance containing the queried anime's data.

    Raises:
        requests.HTTPError: If the HTTP request to the Jikan API fails.

    Example:
        >>> anime = query_anime(9253)
        >>> print(anime.title)
    """

    url = f"https://api.jikan.moe/v4/anime/{id}"
    response = requests.get(url)
    response.raise_for_status()  # if have some problem, raise a error
    # print(json.dumps(response.json(), ensure_ascii=False, indent=2))

    anime_response = AnimeResponse.model_validate(response.json())
    return anime_response.data


if __name__ == "__main__":
    try:
        anime = query_anime(59978)

        print(anime)
        # print(anime.title)
        print(anime.synopsis)
    except Exception as e:
        print(f"Error: {e}")
