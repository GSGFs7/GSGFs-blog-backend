from ninja import Router

from api.auth import AsyncTimeBaseAuth
from api.schemas import ClientIdSchema

router = Router()


@router.get("/me", auth=AsyncTimeBaseAuth(), response={200: ClientIdSchema})
async def get_client_id(request):
    return {"client_id": str(request.auth)}
