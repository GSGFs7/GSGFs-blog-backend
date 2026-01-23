from ninja import Router
from pydantic import PositiveInt

from ..auth import TimeBaseAuth
from ..models import Gal
from ..vndb import query_vn
from ..schemas import (
    GalPaginationResponse,
    GalSchema,
    GalUpdateSchema,
    IdSchema,
    IdsSchema,
    MessageSchema,
)

router = Router()


@router.get(
    "/",
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


@router.get("/ids", response=IdsSchema)
def get_gal_ids(request):
    return {"ids": list(Gal.objects.values_list("id", flat=True))}


@router.get("/{int:gal_id}", response={200: GalSchema, 404: MessageSchema})
def get_gal_from_id(request, gal_id: int):
    try:
        gal = Gal.objects.get(pk=gal_id)
        return gal
    except Gal.DoesNotExist:
        return 404, {"message": "not found"}


@router.post(
    "/{int:gal_id}",
    response={200: IdSchema, 400: MessageSchema, 404: MessageSchema},
    auth=TimeBaseAuth(),
)
def update_gal(request, gal_id: int, body: GalUpdateSchema):
    if gal_id != body.id:
        return 400, {"message": "id not match"}

    try:
        gal = Gal.objects.get(pk=gal_id)

        # 更新字段
        gal.title = body.title
        gal.title_cn = body.title_cn
        gal.character_score = body.character_score
        gal.story_score = body.story_score
        gal.comprehensive_score = body.comprehensive_score
        gal.vndb_rating = body.vndb_rating
        gal.summary = body.summary
        gal.review = body.review
        gal.cover_image = body.cover_image
        # 保存更改
        gal.save()

        return 200, {"id": gal_id}
    except Gal.DoesNotExist:
        return 404, {"message": "not found"}
    except Exception as e:
        return 400, {f"message": "Update failed: {e}"}
