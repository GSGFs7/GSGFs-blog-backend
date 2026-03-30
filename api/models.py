"""
TODO: split this
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from io import BytesIO
from typing import IO

import jieba
from asgiref.sync import sync_to_async
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import models, transaction
from django.utils.text import Truncator, slugify
from pgvector.django import HnswIndex, VectorField
from PIL import Image as PILImage

from api.constants import IMAGE_ALLOWED_FORMAT, POST_RESERVED_SLUGS
from api.exiftool import AsyncExifTool, SyncExifTool
from api.utils import calculate_blake3_hash, chinese_slugify, extract_metadata

logger = logging.getLogger(__name__)


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # django 的元数据选项 表示这是一个用于模板的抽象基类 不会创建数据表 只能由于继承
    # https://docs.djangoproject.com/zh-hans/5.1/topics/db/models/#abstract-base-classes
    class Meta:
        abstract = True

    # 重写delete方法
    # def delete(self, using=None, keep_parents=False):
    #     self.is_deleted = True
    #     self.deleted_at = timezone.now()
    #     self.save()


class Tag(BaseModel):
    name = models.CharField(max_length=100, unique=True, db_index=True, null=False)

    def __str__(self):
        return self.name


class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True, db_index=True, null=False)

    def __str__(self):
        return self.name


class Gal(BaseModel):
    vndb_id = models.CharField(
        blank=False, max_length=10, unique=True, help_text="在VNDB中的ID, 必填"
    )
    title = models.CharField(max_length=100, null=True, blank=True)
    title_cn = models.CharField(max_length=100, null=True, blank=True)

    # score
    character_score = models.FloatField(blank=True, null=True)
    story_score = models.FloatField(blank=True, null=True)
    comprehensive_score = models.FloatField(blank=True, null=True)
    vndb_rating = models.FloatField(blank=True, null=True)

    # review
    summary = models.CharField(
        max_length=200, blank=True, null=True, help_text="显示在外面, 类似于备注"
    )  # No spoilers
    review = models.TextField(blank=True, null=True)
    review_html = models.TextField(blank=True, null=True)

    cover_image = models.URLField(
        max_length=500, blank=True, null=True, help_text="(暂时没用)"
    )

    def __str__(self):
        return self.vndb_id

    def save(self, *args, **kwargs) -> None:
        return super().save(*args, **kwargs)


class Post(BaseModel):
    # 基础信息
    title = models.CharField(
        max_length=50, unique=True, db_index=True, null=False, blank=True
    )
    content = models.TextField(blank=False, null=False, help_text="文章正文, 必填")

    # 渲染后的内容
    content_html = models.TextField(null=True, blank=True, help_text="自动生成")

    # 图片相关
    cover_image = models.URLField(
        max_length=500, blank=True, null=True, help_text="文章封面图片(URL)"
    )
    header_image = models.URLField(
        max_length=500, blank=True, null=True, help_text="文章og显示图片(URL)"
    )  # The only purpose now is as og image in website metadata

    # SEO相关
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        help_text="url 地址 (暂时没用)",
        db_index=True,
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="SEO描述",
    )
    keywords = models.CharField(
        max_length=200, blank=True, help_text="文章关键词，用逗号分隔"
    )

    # 统计
    view_count = models.PositiveIntegerField(default=0, help_text="(暂时没用)")

    # 排序
    order = models.IntegerField(
        default=0, help_text="是否覆盖默认的优先级, 数值越大越靠前"
    )

    # 查询相关
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        # null=True, 本来就可以为空
        default=None,
        related_name="posts",
    )  # tags 可以对多

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=True,  # 在表单中可以为空
        null=True,  # 在数据库中可以为空
        default=None,
        related_name="posts",
    )  # 只能有一个 禁止删除还有文章的分类

    # 文章状态
    status = models.CharField(
        max_length=20,
        # https://docs.djangoproject.com/zh-hans/5.1/ref/models/fields/#choices
        # 强制执行模型验证 需要提供映射关系 第一个是存储的实际值 第二个是人类可读的名称
        choices=[("draft", "草稿"), ("published", "已发布")],
        default="draft",
    )

    # 向量化搜索已迁移至 PostChunk
    # embedding = VectorField(dimensions=768, null=True, blank=True)

    # PG full-text search
    pg_gin_search_vector = SearchVectorField(null=True, blank=True)
    tokenized_content = models.TextField(blank=True, null=True)

    # update in 'api/signals.py'
    content_update_at = models.DateTimeField(
        null=False, blank=True, help_text="文章正文最后更新时间"
    )

    class Meta(BaseModel.Meta):
        ordering = ["-order", "-created_at"]
        indexes = [
            GinIndex(fields=["pg_gin_search_vector"]),
        ]

    def __str__(self):
        return self.title

    # rewrite save action
    # called after adminFrom (at `./admin.py`)
    @transaction.atomic  # keep atomic, all success or all failures
    def save(self, *args, **kwargs):
        post_metadata = extract_metadata(self.content)

        # === title ===
        if not self.title:
            self.title = post_metadata.get("title") or ""

        # === slug ===
        if not self.slug:
            self.slug = post_metadata.get("slug")
        if not self.slug and self.title:
            self.slug = chinese_slugify(self.title)
        if self.slug in POST_RESERVED_SLUGS:
            raise ValidationError(
                f"Slug '{self.slug}' is a reserved keyword and cannot be used."
            )

        # === description ===
        if not self.meta_description:
            self.meta_description = post_metadata.get("description")

        # === keywords ===
        if not self.keywords:
            self.keywords = post_metadata.get("keywords")

        # === image ===
        if not self.cover_image:
            self.cover_image = post_metadata.get("cover_image")
        if not self.header_image:
            self.header_image = post_metadata.get("header_image")

        # === category ===
        if not self.category and post_metadata.get("category"):
            category = post_metadata.get("category")
            category, created = Category.objects.get_or_create(name=category)
            self.category = category

        # === tokenize (PG FTS) ===
        self.tokenized_content = " ".join(jieba.lcut(self.content, cut_all=True))

        # === vector ===
        # Moved to Celery task (see api/tasks.py: generate_post_embedding)
        # The embedding will be generated asynchronously after the post is saved

        # save main object, all settings above will be saved
        # after that, continue to process operations that require primary keys
        super().save(*args, **kwargs)

        # === tags ===
        # NOTE: This logic is already handled in PostAdminForm.clean()
        # However, it's kept here to support non-Admin post creation (e.g. scripts, API)
        # This is safe as it checks `if not self.tags.exists()` before processing
        if not self.tags.exists():  # must use `.exists()` to check it
            tags_to_set = []
            tag_list = post_metadata["tags"]
            for tag_name in tag_list:
                tag_obj, created = Tag.objects.get_or_create(name=tag_name)
                tags_to_set.append(tag_obj)
            self.tags.set(tags_to_set)

        # === Full-text search ===
        # generate PG full-text search vector
        Post.objects.filter(pk=self.pk).update(
            pg_gin_search_vector=SearchVector(
                "title",
                "tokenized_content",
                config="simple",
            )
        )


class PostChunk(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="chunks")
    content = models.TextField()
    embedding = VectorField(dimensions=768)
    chunk_index = models.IntegerField()  # The order of the block in the original text

    class Meta:
        indexes = [
            HnswIndex(
                name="post_chunk_embedding_idx",
                fields=["embedding"],
                m=32,
                ef_construction=256,
                opclasses=["vector_cosine_ops"],
            )
        ]


class Page(BaseModel):
    # 基础信息
    title = models.CharField(max_length=50)
    content = models.TextField()

    # 渲染后的内容
    content_html = models.TextField(null=True, blank=True)

    # 图片相关
    cover_image = models.URLField(
        max_length=500, blank=True, null=True, help_text="文章封面图片(URL)"
    )
    header_image = models.URLField(
        max_length=500, blank=True, null=True, help_text="文章顶部大图(URL)"
    )

    # SEO相关
    slug = models.SlugField(
        max_length=100, unique=True, blank=True, help_text="url 地址", db_index=True
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="SEO描述, 留空将自动生成",
    )
    keywords = models.CharField(
        max_length=200, blank=True, help_text="文章关键词，用逗号分隔"
    )

    # 统计
    view_count = models.PositiveIntegerField(default=0)

    # 排序
    order = models.IntegerField(default=0, help_text="是否覆盖默认的优先级")

    # 查询相关
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        # null=True, 本来就可以为空
        default=None,
        related_name="pages",
    )  # tags 可以对多

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=True,  # 在表单中可以为空
        null=True,  # 在数据库中可以为空
        default=None,
        related_name="pages",
    )  # 只能有一个 禁止删除还有文章的分类

    # 文章状态
    status = models.CharField(
        max_length=20,
        # https://docs.djangoproject.com/zh-hans/5.1/ref/models/fields/#choices
        # 强制执行模型验证 需要提供映射关系 第一个是存储的实际值 第二个是人类可读的名称
        choices=[("draft", "草稿"), ("published", "已发布")],
        default="draft",
    )

    class Meta(BaseModel.Meta):
        ordering = ["-order", "-created_at"]

    def __str__(self):
        return self.title

    # 重写保存时的操作
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        if not self.meta_description:
            # 需要再次确认小于160个
            self.meta_description = Truncator(self.content).chars(150, html=True)[:160]

        if not self.keywords:
            self.keywords = extract_metadata(self.content).get("keywords")

        return super().save(*args, **kwargs)


class Guest(BaseModel):
    class Providers(models.TextChoices):
        github = "github", "github"
        google = "google", "google"
        myself = "myself", "myself"
        osu = "osu", "osu"

    name = models.CharField(max_length=50)
    # unique_id 就是 "provider" + "-" + "provider_id"
    unique_id = models.CharField(max_length=50, unique=True, db_index=True)  # 添加索引
    email = models.EmailField()
    password = models.CharField(max_length=128)
    provider = models.CharField(
        max_length=10, choices=Providers, default=Providers.myself
    )
    provider_id = models.IntegerField()
    avatar = models.URLField(max_length=200)
    is_admin = models.BooleanField(default=False)
    last_visit = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Comment(BaseModel):
    content = models.TextField(max_length=10000)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name="comments")

    # 用户信息
    user_agent = models.CharField(max_length=100, blank=True, default="unknown")
    OS = models.CharField(max_length=100, blank=True, default="unknown")
    platform = models.CharField(max_length=100, blank=True, default="unknown")
    browser = models.CharField(max_length=100, blank=True, default="unknown")
    browser_version = models.CharField(max_length=100, blank=True, default="unknown")

    def __str__(self):
        return self.content[:10]


class Anime(BaseModel):
    mal_id = models.IntegerField(blank=False, help_text="在MyAnimeList中的ID, 必填")
    name = models.CharField(
        max_length=100, blank=True, null=False, unique=True, db_index=True
    )
    name_cn = models.CharField(max_length=100, blank=True, null=True)
    year = models.IntegerField(default=None, blank=True, null=True)
    synopsis = models.TextField(default=None, blank=True, null=True)
    cover_image = models.URLField(max_length=500, blank=True, null=True)
    # https://en.wikipedia.org/wiki/Motion_Picture_Association_film_rating_system
    rating = models.CharField(blank=True, null=True)

    # fill it by your self
    score = models.FloatField(blank=True, null=True)
    review = models.TextField(blank=True, null=True)

    class Meta(BaseModel.Meta):
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


def image_raw_upload_path(instance: "ImageResource", filename: str) -> str:
    """
    Generate upload path for images using checksum-based directory structure.
    Prevent too many files in a single directory by sharding into sub dirs.
    """
    ext = os.path.splitext(filename)[1].lower()
    return (
        f"images/raw/"
        f"{instance.checksum[:2]}/"
        f"{instance.checksum[2:4]}/"
        f"{instance.checksum}{ext}"
    )


def image_thumbnail_upload_path(instance: "ImageResource", filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
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
    @staticmethod
    def create_from_file(
        content: IO[bytes], filename: str
    ) -> tuple["Image", ImageResource, bool]:

        # NOTE: There are some problem here
        #  1. image workflow is too long & complex, sync blocking in front, reduce QPS.
        #  2. if calculate hash only, EXIF clean and duplicates removing will invalid,
        #     and hash remap is too unelegant.
        #  Feature-rich & High-concurrency can't have it both ways?
        #  just like CAP theorem?

        # 0. extract basic info and verify file integrity
        try:
            width, height, mime_type = Image._process_image_verify(content)
        except Exception:
            raise ValidationError("Unrecognizable image file or file is corrupted")

        # TODO: some photography may needs keep some EXIF
        # 1. clean metadata
        try:
            cleaned_io, size = Image._process_clean_metadata(content, filename)
            del content
        except Exception as e:
            logger.warning(f"Could not process image: {e}")
            raise ValidationError("Could not clean image metadata")

        # 2. checksum
        checksum = Image._calculate_file_checksum(cleaned_io)

        # 3. write to db
        res_meta = ImageResource.ImageResourceMeta(width, height, size, mime_type)
        return Image._create_from_file__write_db(
            cleaned_io=cleaned_io,
            checksum=checksum,
            filename=filename,
            res_meta=res_meta,
        )

    @staticmethod
    async def acreate_from_file(
        content: IO[bytes], filename: str
    ) -> tuple["Image", ImageResource, bool]:
        # 0. verify
        width, height, mime_type = await Image._aprocess_image_verify(content)

        # 1. clean EXIF data
        try:
            cleaned_io, size = await Image._aprocess_clean_metadata(content, filename)
            del content
        except Exception as e:
            logger.warning(f"Could not process image (async): {e}")
            raise ValidationError("Could not clean image metadata")

        # 2. checksum
        checksum = await Image._acalculate_file_checksum(cleaned_io)

        # 3. write to db
        res_meta = ImageResource.ImageResourceMeta(width, height, size, mime_type)
        return await Image._acreate_from_file__write_db(
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

    @staticmethod
    async def _aprocess_image_verify(content: IO[bytes]) -> tuple[int, int, str]:
        return await asyncio.to_thread(Image._process_image_verify, content)

    # --- clean metadata ---

    @staticmethod
    def _process_clean_metadata_fallback(content: IO[bytes]) -> tuple[BytesIO, int]:
        img = PILImage.open(content)
        cleaned_io = BytesIO()
        img.save(cleaned_io, quality=100, save_all=True, format=img.format)
        size = cleaned_io.getbuffer().nbytes
        return cleaned_io, size

    @staticmethod
    def _process_clean_metadata(content: IO[bytes], filename) -> tuple[BytesIO, int]:
        content.seek(0)
        if SyncExifTool.is_available():
            # SyncExifTool, no PIL re-encoding, more efficient
            cleaned_io = SyncExifTool().clean(content, filename=filename)
            size = cleaned_io.getbuffer().nbytes
            return cleaned_io, size
        # fallback
        return Image._process_clean_metadata_fallback(content)

    @staticmethod
    async def _aprocess_clean_metadata(
        content: IO[bytes], filename: str
    ) -> tuple[BytesIO, int]:
        content.seek(0)
        if await AsyncExifTool().is_available():
            cleaned_io = await AsyncExifTool().clean(content, filename)
            size = cleaned_io.getbuffer().nbytes
            return cleaned_io, size
        return await asyncio.to_thread(Image._process_clean_metadata_fallback, content)

    # --- checksum ---

    @staticmethod
    def _calculate_file_checksum(cleaned_io: IO) -> str:
        return calculate_blake3_hash(cleaned_io)

    @staticmethod
    async def _acalculate_file_checksum(cleaned_io: IO) -> str:
        return await asyncio.to_thread(calculate_blake3_hash, cleaned_io)

    # --- db ---

    @staticmethod
    @transaction.atomic
    def _create_from_file__write_db(
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
        img = Image.objects.create(
            resource=img_res,
            original_name=filename,
            # TODO: add user context here
            uploaded_by=None,
            alt_text="",
            description="",
        )
        return img, img_res, created

    @staticmethod
    async def _acreate_from_file__write_db(
        *,
        cleaned_io: BytesIO,
        checksum: str,
        filename: str,
        res_meta: ImageResource.ImageResourceMeta,
    ) -> tuple["Image", ImageResource, bool]:
        return await sync_to_async(Image._create_from_file__write_db)(
            cleaned_io=cleaned_io,
            checksum=checksum,
            filename=filename,
            res_meta=res_meta,
        )
