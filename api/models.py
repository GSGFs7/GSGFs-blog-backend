from django.db import models
from django.utils import timezone
from django.utils.text import Truncator, slugify

from .utils import extract_keywords


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

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
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Gal(BaseModel):
    vndb_id = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=100, null=True, blank=True)
    title_cn = models.CharField(max_length=100, null=True, blank=True)

    # score
    character_score = models.FloatField(blank=True, null=True)
    story_score = models.FloatField(blank=True, null=True)
    comprehensive_score = models.FloatField(blank=True, null=True)
    vndb_rating = models.FloatField(blank=True, null=True)

    # review
    summary = models.CharField(max_length=200, blank=True, null=True)  # No spoilers
    review = models.TextField(blank=True, null=True)

    cover_image = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.vndb_id

    def save(self, *args, **kwargs) -> None:
        return super().save(*args, **kwargs)


class Post(BaseModel):
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
        related_name="post",
    )  # tags 可以对多

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=True,  # 在表单中可以为空
        null=True,  # 在数据库中可以为空
        default=None,
        related_name="post",
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
    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.slug:
            self.slug = slugify(self.title)

        if not self.meta_description:
            self.meta_description = Truncator(self.content).chars(150, html=True)[:160]

        if not self.keywords:
            self.keywords = extract_keywords(self.content)

        return super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


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
    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.slug:
            self.slug = slugify(self.title)

        if not self.meta_description:
            # 需要再次确认小于160个
            self.meta_description = Truncator(self.content).chars(150, html=True)[:160]

        if not self.keywords:
            self.keywords = extract_keywords(self.content)

        return super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


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
    provider = models.CharField(choices=Providers, max_length=10, default="myself")
    provider_id = models.IntegerField()
    avatar = models.URLField(max_length=200)
    is_admin = models.BooleanField(default=False)
    last_visit = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Comment(BaseModel):
    content = models.TextField(max_length=10000)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comment")
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name="comment")

    # 用户信息
    user_agent = models.CharField(max_length=100, blank=True, default="unknown")
    OS = models.CharField(max_length=100, blank=True, default="unknown")
    platform = models.CharField(max_length=100, blank=True, default="unknown")
    browser = models.CharField(max_length=100, blank=True, default="unknown")
    browser_version = models.CharField(max_length=100, blank=True, default="unknown")

    def __str__(self):
        return self.content[:10]
