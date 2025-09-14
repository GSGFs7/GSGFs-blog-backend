from ninja import Router

from ..auth import TimeBaseAuth
from ..schemas import MessageSchema

router = Router()


@router.get("/auth", auth=TimeBaseAuth(), response=MessageSchema)
def test_auth(request):
    return {"message": "authenticated"}
