from typing import Optional

from ninja import Schema


class ImageUploadRequestSchema(Schema):
    # TODO
    pass


class ImageUploadResponseSchema(Schema):
    id: int
    url: str
    width: Optional[int]
    height: Optional[int]
    original_name: str
