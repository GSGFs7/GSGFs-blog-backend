from django.db import models
from django.utils import timezone
from django.utils.text import Truncator, slugify


class BaseModel(models.Model):
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


class Author(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    email = models.EmailField()

    def __str__(self):
        return self.name


class Post(BaseModel):
    # 基础信息
    title = models.CharField(max_length=50)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now_add=True)

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
        max_length=100, unique=True, blank=True, help_text="url 地址"
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="SEO描述, 留空将自动生成",
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
    author = models.ForeignKey(
        Author,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        default=None,
        related_name="post",  # 可以通过对方来查询自己
    )
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

    class Meta:
        ordering = ["-order", "-created_at"]

    def __str__(self):
        return self.title

    # 重写保存时的操作
    def save(
        self, using=None, force_insert=False, force_update=False, update_fields=None
    ):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.meta_description:
            self.meta_description = Truncator(self.content).chars(150, html=True)
        return super().save(force_insert, force_update, using, update_fields)


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
    is_admin = models.BooleanField(default=False)
    as_author = models.ForeignKey(
        Author,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        default=None,
        related_name="user",
    )

    def __str__(self):
        return self.name


class Comment(BaseModel):
    content = models.TextField(max_length=10000)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comment")
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name="comment")
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content[:10]
