from ninja import Router

from api.auth import TimeBaseAuth
from api.schemas import ClientIdSchema

router = Router()


@router.get("/me", auth=TimeBaseAuth(), response={200: ClientIdSchema})
async def get_client_id(request):
    return {"client_id": str(request.auth)}
