from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.text import Truncator, slugify
from pgvector.django import VectorField

from .utils import chinese_slugify, extract_metadata


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

    # 向量化搜索
    embedding = VectorField(dimensions=768, null=True, blank=True)

    # update in 'api/signals.py'
    content_update_at = models.DateTimeField(
        null=False, blank=True, help_text="文章正文最后更新时间"
    )

    class Meta(BaseModel.Meta):
        ordering = ["-order", "-created_at"]

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
        RESERVED_SLUGS = ["posts", "sitemap", "search", "post", "all", "query", "ids"]
        if self.slug in RESERVED_SLUGS:
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

        # === vector ===
        # Moved to Celery task (see api/tasks.py: generate_post_embedding)
        # The embedding will be generated asynchronously after the post is saved

        # save main object, all settings above will be saved
        # after that, continue to process operations that require primary keys
        super().save(*args, **kwargs)

        # === tags ===
        # TODO
        # it not work! WTF???
        if not self.tags.exists():  # must use `.exists()` to check it
            tags_to_set = []
            tag_list = post_metadata["tags"]
            for tag_name in tag_list:
                tag_obj, created = Tag.objects.get_or_create(name=tag_name)
                tags_to_set.append(tag_obj)
            self.tags.set(tags_to_set)


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


# class Image(BaseModel):
#     title = models.CharField(
#         max_length=100, blank=True, null=True, help_text="图片标题"
#     )
#     description = models.TextField(blank=True, null=True, help_text="图片描述")
#     file_name = models.CharField(max_length=100, unique=True, help_text="图片文件名")
#     file_size = models.PositiveIntegerField(help_text="图片文件大小（字节）")
#     file_type = models.CharField(max_length=50, help_text="图片文件类型")
#     url = models.URLField(max_length=500, help_text="图片URL地址")

#     class Meta(BaseModel.Meta):
#         ordering = ["-created_at"]

#     def __str__(self):
#         return self.title or self.file_name
