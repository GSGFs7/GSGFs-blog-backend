from ninja import Router

from ..auth import TimeBaseAuth
from ..models import Guest
from ..schemas import GuestLoginSchema, GuestSchema, IdSchema, MessageSchema

router = Router()


@router.post("/guest/login", response=IdSchema, auth=TimeBaseAuth)
def guest_login(request, body: GuestLoginSchema):
    try:
        guest = Guest.objects.get(unique_id=f"{body.provider}-{body.provider_id}")

        guest.avatar = body.avatar_url
        guest.name = body.name
        guest.save()
    except:
        guest = Guest.objects.create(
            unique_id=f"{body.provider}-{body.provider_id}",
            provider=body.provider,
            provider_id=body.provider_id,
            name=body.name,
            avatar=body.avatar_url,
        )
    return guest


@router.get(
    "/guest/{int:guest_id}",
    response={200: GuestSchema, 404: MessageSchema},
    auth=TimeBaseAuth(),
)
def get_guest(request, guest_id: int):
    try:
        guest = Guest.objects.get(pk=guest_id)
        return guest
    except:
        return 404, {"message": "Not found"}
