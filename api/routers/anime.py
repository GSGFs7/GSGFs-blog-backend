from ninja import Router
from pydantic import PositiveInt

from api.models import Anime
from api.schemas import AnimeIds, AnimeSchema, MessageSchema

router = Router()


@router.get("/", response={200: AnimeIds, 400: MessageSchema, 404: MessageSchema})
def get_all_anime_ids(request, page: PositiveInt = 1, size: PositiveInt = 10):
    offset = (page - 1) * size
    total = Anime.objects.count()

    if total == 0:
        return 404, {"message": "Empty"}

    if offset >= total:
        return 400, {"message": "Out of range"}

    anime = Anime.objects.all()[offset : offset + size]
    print(anime)
    return 200, {
        "ids": anime,
        "pagination": {
            "total": total,
            "page": page,
            "size": size,
        },
    }


@router.get("/{int:anime_id}", response={200: AnimeSchema, 404: MessageSchema})
def get_anime(request, anime_id: int):
    try:
        anime = Anime.objects.get(pk=anime_id)
        return anime
    except Anime.DoesNotExist:
        return 404, {"message": "Not found"}
