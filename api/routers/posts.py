from ninja import Router
from django.core.cache import cache
from django.conf import settings
from pydantic import PositiveInt

from ..models import Post
from ..schemas import MessageSchema, PostIdsForSitemap, PostsCardsSchema, PostsSchema


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


@router.get("/ids")
def get_all_post_ids(request):
    # QuerySet的values_list()方法与values类似
    # 不过返回的是一个元组而非字典
    # flat可以使返回一个值时返回那个值而非一元组
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
    return PostIdsForSitemap(root=list(posts))
