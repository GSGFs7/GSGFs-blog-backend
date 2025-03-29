from ninja import Router
from pydantic import PositiveInt

from typing import List
from ..models import Gal
from ..schemas import IdsSchema, MessageSchema, GalPaginationResponse

router = Router()


@router.get("/ids", response=IdsSchema)
def get_gal_ids(request):
    return {"ids": list(Gal.objects.values_list("id", flat=True))}


@router.get(
    "/gals",
    response={200: GalPaginationResponse, 400: MessageSchema, 404: MessageSchema},
)
def get_all_gal(request, page: PositiveInt = 1, size: PositiveInt = 10):
    offset = (page - 1) * size
    total = Gal.objects.count()

    if total == 0:
        return 404, {"message": "Empty"}

    if offset >= total:
        return 400, {"message": "Out of range"}

    gals = Gal.objects.all()[offset : offset + size]
    return 200, {
        "gals": list(gals),
        "pagination": {
            "total": total,
            "page": page,
            "size": size,
        },
    }
