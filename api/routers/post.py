from django.conf import settings
from django.core.cache import cache
from ninja import Router
from pydantic import PositiveInt

from ..auth import TimeBaseAuth
from ..models import Category, Post, Tag
from ..schemas import (
    IdsSchema,
    MessageSchema,
    PostIdsForSitemap,
    PostsCardsSchema,
    PostSitemapSchema,
    PostsSchema,
    RenderSchema,
)

router = Router()


@router.get(
    "/posts", response={200: PostsCardsSchema, 400: MessageSchema, 404: MessageSchema}
)
def get_posts(request, page: PositiveInt = 1, size: PositiveInt = 10):
    offset = (page - 1) * size  # 起点
    total = Post.objects.count()

    if total == 0:
        return 404, {"message": "Empty"}

    if offset >= total:
        return 400, {"message": "Out of range"}

    posts = Post.objects.all()[offset : offset + size]
    return 200, {
        "posts": list(posts),
        "pagination": {
            "total": total,  # 一共有多少个
            "page": page,  # 当前是第几页
            "size": size,  # 一页的数量
        },
    }


@router.get("/", response=IdsSchema)
def get_all_post_ids(request):
    # QuerySet的values_list()方法与values类似
    # 不过返回的是一个元组而非字典
    # flat可以使返回一个值时返回那个值而非一个一元组
    # print(Post.objects.values_list("id", flat=True))
    return {"ids": list(Post.objects.values_list("id", flat=True))}


@router.get("/{int:post_id}", response={200: PostsSchema, 404: MessageSchema})
def get_post(request, post_id: int):
    # cache_key = f"post:{post_id}"
    # post_data = cache.get(cache_key)

    # if not post_data:
    #     try:
    #         post = Post.objects.get(pk=post_id)
    #         cache.set(cache_key, post, settings.CACHE_TTL)
    #         return post
    #     except Post.DoesNotExist:
    #         return 404, {"message": "Not found"}
    # return post_data

    try:
        post = Post.objects.get(pk=post_id)
        return post
    except Post.DoesNotExist:
        return 404, {"message": "Not found"}


@router.get("/sitemap", response=PostIdsForSitemap)
def get_all_post_ids_for_sitemap(request):
    posts = Post.objects.values("id", "slug", "update_at")
    # transform to Pydantic model
    post_schemas = [PostSitemapSchema(**post) for post in posts]
    return PostIdsForSitemap(root=post_schemas)


# @router.post("/render", auth=TimeBaseAuth())
# def render(request, body: RenderSchema):
#     post = Post.objects.get(pk=body.id)
#     fields = body.dict(exclude={"id"})
#     # print(fields)
#
#     if fields.get("content_html") is not None:
#         post.content_html = fields.get("content_html")
#
#     if fields.get("cover_image") is not None:
#         post.cover_image = fields.get("cover_image")
#
#     if fields.get("header_image") is not None:
#         post.header_image = fields.get("header_image")
#
#     slug_value = fields.get("slug")
#     if slug_value is not None:
#         post.slug = str(slug_value)
#
#     meta_description_value = fields.get("meta_description")
#     if meta_description_value is not None:
#         post.meta_description = meta_description_value
#
#     # 处理分类
#     if fields.get("category") is not None:
#         category_name = fields.get("category")
#         category, category_created = Category.objects.get_or_create(name=category_name)
#         post.category = category
#
#     # 处理标签
#     if fields.get("tags") is not None:
#         new_tags = []
#         name_of_tags = fields.get("tags", [])
#         for tag_name in name_of_tags:
#             new_tag, tags_created = Tag.objects.get_or_create(name=tag_name)
#             new_tags.append(new_tag)
#         post.tags.set(new_tags)
#
#     post.save()
