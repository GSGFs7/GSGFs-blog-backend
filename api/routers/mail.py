from django.core.mail import send_mail, send_mass_mail
from ninja import Router

router = Router()


@router.get("/")
def test_mail(request):
    pass
