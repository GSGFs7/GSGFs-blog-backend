import logging

from django.conf import settings
from ninja import Router, UploadedFile

from api.auth import AsyncTimeBaseAuth
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
    auth=AsyncTimeBaseAuth(),
)
async def upload_test(
    request,
    file: UploadedFile,
    data: ImageUploadRequestSchema | None = None,
):
    if file.content_type not in IMAGE_ALLOWED_FORMAT:
        return 400, {"message": "not allowed image types"}

    if file.size > settings.IMAGE_UPLOAD_MAX_SIZE:
        return 400, {"message": "image size exceeds maximum limit"}

    img, img_res, _ = await Image.acreate_from_file(file, filename=file.name)

    return 201, ImageUploadResponseSchema(
        id=img.id,
        url=img_res.file.url,
        width=img_res.width,
        height=img_res.height,
        original_name=img.original_name,
    )
