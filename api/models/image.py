# TODO: remove this to a new django app

import asyncio
import logging
import os
from dataclasses import dataclass
from io import BytesIO
from typing import IO

from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import models, transaction
from PIL import Image as PILImage

from api.constants import IMAGE_ALLOWED_FORMAT
from api.exiftool import AsyncExifTool, SyncExifTool
from api.utils import calculate_blake3_hash

from .base import BaseModel

logger = logging.getLogger(__name__)


# image resource upload path. do not make any changes.
# Django ORM may break (because 0047 migration hardcode the function path)
# or, move there functions into 0047 migration?
def image_raw_upload_path(instance: "ImageResource", filename: str) -> str:
    """
    Generate upload path for images using checksum-based directory structure.
    Prevent too many files in a single directory by sharding into sub dirs.
    """
    ext = os.path.splitext(filename)[-1].lower()
    return (
        f"images/raw/"
        f"{instance.checksum[:2]}/"
        f"{instance.checksum[2:4]}/"
        f"{instance.checksum}{ext}"
    )


def image_thumbnail_upload_path(instance: "ImageResource", filename: str) -> str:
    ext = os.path.splitext(filename)[-1].lower()
    return (
        f"images/thumbnails/"
        f"{instance.checksum[:2]}/"
        f"{instance.checksum[2:4]}/"
        f"{instance.checksum}{ext}"
    )


def image_avif_upload_path(instance: "ImageResource", filename: str) -> str:
    return (
        f"images/avif/"
        f"{instance.checksum[:2]}/"
        f"{instance.checksum[2:4]}/"
        f"{instance.checksum}.avif"
    )


def image_webp_upload_path(instance: "ImageResource", filename: str) -> str:
    return (
        f"images/webp/"
        f"{instance.checksum[:2]}/"
        f"{instance.checksum[2:4]}/"
        f"{instance.checksum}.webp"
    )


class ImageResource(BaseModel):
    """
    single physical file
    """

    # checksum
    checksum = models.CharField(max_length=64, unique=True)

    # TODO: s3
    # files
    file = models.ImageField(upload_to=image_raw_upload_path, null=False, blank=False)
    # other files auto generate by django signal & celery task
    avif_file = models.ImageField(
        upload_to=image_avif_upload_path, null=True, blank=True
    )
    webp_file = models.ImageField(
        upload_to=image_webp_upload_path, null=True, blank=True
    )
    thumbnail = models.ImageField(
        upload_to=image_thumbnail_upload_path, null=True, blank=True
    )

    # attribute
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=50)

    is_processed = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["checksum"])]

    @dataclass
    class ImageResourceMeta:
        width: int
        height: int
        size: int
        mime_type: str


# Create your models here.
class Image(BaseModel):
    """
    logical image file
    """

    resource = models.ForeignKey(
        ImageResource, on_delete=models.CASCADE, related_name="references"
    )

    # image file info
    original_name = models.CharField(max_length=255, blank=True, null=False)

    # who
    uploaded_by = models.ForeignKey(
        "api.Guest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="images",
    )

    # Markdown meta info
    alt_text = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    # image metadata
    metadata = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.original_name or f"Image {self.id}"

    @property
    def url(self) -> str:
        return self.resource.file.url

    # DRY principle
    # read: https://docs.djangoproject.com/en/6.0/misc/design-philosophies/#don-t-repeat-yourself-dry
    @classmethod
    def create_from_file(
        cls, content: IO[bytes], filename: str
    ) -> tuple["Image", ImageResource, bool]:

        # NOTE: There are some problem here
        #  1. image workflow is too long & complex, sync blocking in front, reduce QPS.
        #  2. if calculate hash only, EXIF clean and duplicates removing will invalid,
        #     and hash remap is too unelegant.
        #  Feature-rich & High-concurrency can't have it both ways?
        #  just like CAP theorem?

        # 0. extract basic info and verify file integrity
        try:
            width, height, mime_type = cls._process_image_verify(content)
        except Exception:
            raise ValidationError("Unrecognizable image file or file is corrupted")

        # TODO: some photography may needs keep some EXIF
        # 1. clean metadata
        try:
            cleaned_io, size = cls._process_clean_metadata(content, filename)
            del content
        except Exception as e:
            logger.warning(f"Could not process image: {e}")
            raise ValidationError("Could not clean image metadata")

        # 2. checksum
        checksum = cls._calculate_file_checksum(cleaned_io)

        # 3. write to db
        res_meta = ImageResource.ImageResourceMeta(width, height, size, mime_type)
        return cls._create_from_file__write_db(
            cleaned_io=cleaned_io,
            checksum=checksum,
            filename=filename,
            res_meta=res_meta,
        )

    @classmethod
    async def acreate_from_file(
        cls, content: IO[bytes], filename: str
    ) -> tuple["Image", ImageResource, bool]:
        # 0. verify
        width, height, mime_type = await cls._aprocess_image_verify(content)

        # 1. clean EXIF data
        try:
            cleaned_io, size = await cls._aprocess_clean_metadata(content, filename)
            del content
        except Exception as e:
            logger.warning(f"Could not process image (async): {e}")
            raise ValidationError("Could not clean image metadata")

        # 2. checksum
        checksum = await cls._acalculate_file_checksum(cleaned_io)

        # 3. write to db
        res_meta = ImageResource.ImageResourceMeta(width, height, size, mime_type)
        return await cls._acreate_from_file__write_db(
            cleaned_io=cleaned_io,
            checksum=checksum,
            filename=filename,
            res_meta=res_meta,
        )

    # --- verify ---

    @staticmethod
    def _process_image_verify(content: IO[bytes]) -> tuple[int, int, str]:
        content.seek(0)
        with PILImage.open(content) as img:
            width, height = img.size
            mime_type = PILImage.MIME.get(img.format)
            if mime_type not in IMAGE_ALLOWED_FORMAT:
                raise ValidationError("Not allowed image types")
            img.verify()
            return width, height, mime_type

    @classmethod
    async def _aprocess_image_verify(cls, content: IO[bytes]) -> tuple[int, int, str]:
        return await asyncio.to_thread(cls._process_image_verify, content)

    # --- clean metadata ---

    @staticmethod
    def _process_clean_metadata_fallback(content: IO[bytes]) -> tuple[BytesIO, int]:
        img = PILImage.open(content)
        cleaned_io = BytesIO()
        img.save(cleaned_io, quality=100, save_all=True, format=img.format)
        size = cleaned_io.getbuffer().nbytes
        return cleaned_io, size

    @classmethod
    def _process_clean_metadata(
        cls, content: IO[bytes], filename
    ) -> tuple[BytesIO, int]:
        content.seek(0)
        if SyncExifTool.is_available():
            # SyncExifTool, no PIL re-encoding, more efficient
            cleaned_io = SyncExifTool().clean(content, filename=filename)
            size = cleaned_io.getbuffer().nbytes
            return cleaned_io, size
        # fallback
        return cls._process_clean_metadata_fallback(content)

    @classmethod
    async def _aprocess_clean_metadata(
        cls, content: IO[bytes], filename: str
    ) -> tuple[BytesIO, int]:
        content.seek(0)
        if await AsyncExifTool().is_available():
            cleaned_io = await AsyncExifTool().clean(content, filename)
            size = cleaned_io.getbuffer().nbytes
            return cleaned_io, size
        return await asyncio.to_thread(cls._process_clean_metadata_fallback, content)

    # --- checksum ---

    @staticmethod
    def _calculate_file_checksum(cleaned_io: IO) -> str:
        return calculate_blake3_hash(cleaned_io)

    @staticmethod
    async def _acalculate_file_checksum(cleaned_io: IO) -> str:
        return await asyncio.to_thread(calculate_blake3_hash, cleaned_io)

    # --- db ---

    @classmethod
    @transaction.atomic
    def _create_from_file__write_db(
        cls,
        *,
        cleaned_io: BytesIO,
        checksum: str,
        filename: str,
        res_meta: ImageResource.ImageResourceMeta,
    ) -> tuple["Image", ImageResource, bool]:
        cleaned_io.seek(0)
        img_res, created = ImageResource.objects.get_or_create(
            checksum=checksum,
            defaults={
                "file": File(cleaned_io, name=filename),
                "width": res_meta.width,
                "height": res_meta.height,
                "size": res_meta.size,
                "mime_type": res_meta.mime_type,
            },
        )
        img = cls.objects.create(
            resource=img_res,
            original_name=filename,
            # TODO: add user context here
            uploaded_by=None,
            alt_text="",
            description="",
        )
        return img, img_res, created

    @classmethod
    async def _acreate_from_file__write_db(
        cls,
        *,
        cleaned_io: BytesIO,
        checksum: str,
        filename: str,
        res_meta: ImageResource.ImageResourceMeta,
    ) -> tuple["Image", ImageResource, bool]:
        return await sync_to_async(cls._create_from_file__write_db)(
            cleaned_io=cleaned_io,
            checksum=checksum,
            filename=filename,
            res_meta=res_meta,
        )
