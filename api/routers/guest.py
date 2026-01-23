from ninja import Router

from ..auth import TimeBaseAuth
from ..models import Guest
from ..schemas import GuestLoginSchema, GuestSchema, IdSchema, MessageSchema

router = Router()


@router.post("/login", response=IdSchema, auth=TimeBaseAuth())
def guest_login(request, body: GuestLoginSchema):
    unique_id = f"{body.provider}-{body.provider_id}"

    guest, created = Guest.objects.get_or_create(
        unique_id=unique_id,
        provider=body.provider,
        provider_id=body.provider_id,
        name=body.name,
        avatar=body.avatar,
    )

    if not created:
        guest.avatar = body.avatar
        guest.name = body.name
        guest.save()

    return guest


@router.get(
    "/{int:guest_id}",
    response={200: GuestSchema, 404: MessageSchema},
    auth=TimeBaseAuth(),
)
def get_guest(request, guest_id: int):
    try:
        guest = Guest.objects.get(pk=guest_id)
        return guest
    except Guest.DoesNotExist:
        return 404, {"message": "Not found"}
