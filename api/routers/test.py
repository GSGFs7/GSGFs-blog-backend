from ninja import Router

from ..auth import TimeBaseAuth
from ..schemas import MessageSchema

router = Router()


@router.get("/", auth=TimeBaseAuth(), response=MessageSchema)
def test_auth():
    return {"message": "authenticated"}
