from ninja import Router

from ..models import Page
from ..schemas import IdsSchema

router = Router()


@router.get("/ids", response=IdsSchema)
def get_all_page_ids(request):
    return {"ids": list(Page.objects.values_list("id", flat=True))}


@router.get("/{int:page_id}")
def get_page_by_id(request, page_id: int):
    pass
