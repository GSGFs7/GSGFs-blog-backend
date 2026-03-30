from django.db import models
from django.utils.text import Truncator, slugify

from api.utils import extract_metadata

from .base import BaseModel
from .category import Category
from .tag import Tag


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
