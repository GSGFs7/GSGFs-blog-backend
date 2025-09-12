from django.conf import settings
from django.core.cache import cache
from ninja import Router
from pgvector.django import CosineDistance
from pydantic import PositiveInt

from ..ml_model import get_sentence_transformer_model
from ..models import Post
from ..schemas import (
    IdsSchema,
    MessageSchema,
    PostCardsSchema,
    PostCardsWithSimilaritySchema,
    PostIdsForSitemap,
    PostSitemapSchema,
    PostsSchema,
)

CONFIDENCE = 0.3

router = Router()


@router.get(
    "/posts", response={200: PostCardsSchema, 400: MessageSchema, 404: MessageSchema}
)
def get_posts(
        request, page: PositiveInt = 1, size: PositiveInt = 10
):  # -> tuple[Literal[404], dict[str, str]] | tuple[Literal[400],...:
    offset = (page - 1) * size  # 起点
    total = Post.objects.count()

    if total == 0:
        return 404, {"message": "Empty"}

    if offset >= total:
        return 400, {"message": "Out of range"}

    posts = Post.objects.all()[offset: offset + size]
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
    posts = Post.objects.values("id", "slug", "updated_at")
    # transform to Pydantic model
    post_schemas = [PostSitemapSchema(**post) for post in posts]
    return PostIdsForSitemap(root=post_schemas)


@router.get(
    "/search", response={200: PostCardsWithSimilaritySchema, 400: MessageSchema}
)
def get_post_ids_from_query(
        request,
        q: str,
        page: PositiveInt = 1,
        size: PositiveInt = 10,
):
    # cache
    cache_key = f"post_search_results:{hash(q)}"
    cached = cache.get(cache_key)

    # find cache
    if cached is None:
        model = get_sentence_transformer_model()
        query_embedding = model.encode_query(q)
        post_query = (
            Post.objects.annotate(
                similarity=1 - CosineDistance("embedding", query_embedding)
            )
            .filter(similarity__gt=CONFIDENCE)
            .order_by("-similarity")
            .values_list("id", "similarity")
        )
        result = list(post_query)
        cache.set(cache_key, result, timeout=3600)  # 1h
    else:
        result = cached

    # paginate
    total = len(result)
    offset = (page - 1) * size
    paginated_result = result[offset: offset + size]

    # if empty
    if not paginated_result:
        return 200, {
            "posts_with_similarity": [],
            "pagination": {"total": total, "page": page, "size": size},
        }

    # Assemble into corresponding structure
    paginated_ids = [item[0] for item in paginated_result]
    posts_dict = Post.objects.in_bulk(paginated_ids)
    posts_with_similarity = []
    for post_id, similarity in paginated_result:
        post_obj = posts_dict.get(post_id)
        if post_obj:
            posts_with_similarity.append({"post": post_obj, "similarity": similarity})

    return 200, {
        "posts_with_similarity": posts_with_similarity,
        "pagination": {"total": total, "page": page, "size": size},
    }
