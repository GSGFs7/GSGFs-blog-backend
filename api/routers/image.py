import logging
from io import BytesIO

from ninja import Router, UploadedFile

from api.auth import TimeBaseAuth
from api.constants import IMAGE_ALLOWED_FORMAT
from api.models import Image
from api.schemas import (
    ImageUploadRequestSchema,
    ImageUploadResponseSchema,
    MessageSchema,
)

router = Router()
logger = logging.getLogger(__name__)


# Simplified upload handler using model-level file deduplication.
# This allows creating multiple DB entries for the same physical file.
@router.post(
    "/upload",
    response={201: ImageUploadResponseSchema, 400: MessageSchema},
    auth=TimeBaseAuth(),
)
def upload_test(
    request,
    file: UploadedFile,
    data: ImageUploadRequestSchema | None = None,
):
    if file.content_type not in IMAGE_ALLOWED_FORMAT:
        return 400, {"message": "not allowed image types"}

    file.seek(0)
    content = BytesIO(file.read())

    img, img_res = Image.create_from_file(content, filename=file.name)

    return 201, ImageUploadResponseSchema(
        id=img.id,
        url=img_res.file.url,
        width=img_res.width,
        height=img_res.height,
        original_name=img.original_name,
    )
