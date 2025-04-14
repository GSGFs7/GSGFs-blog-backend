from ninja import Router

from ..auth import JWTAuth, TimeBaseAuth
from ..schemas import TokenSchema

router = Router()


@router.get("/login", response={200: TokenSchema}, auth=TimeBaseAuth())
def JWT_login(request):
    token = JWTAuth.create_token()
    return 200, {"token": token, "token_type": "bearer"}
