import logging

from django.core.cache import cache
from ninja import Router
from pgvector.django import CosineDistance
from pydantic import PositiveInt

from api.rate_limit import rate_limit
from api.tasks import generate_search_embedding_task

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

CONFIDENCE = 0.6

router = Router()


@router.get("/", response={200: PostCardsSchema, 400: MessageSchema})
def get_posts(
    request, page: PositiveInt = 1, size: PositiveInt = 10
):  # -> tuple[Literal[404], dict[str, str]] | tuple[Literal[400],...:
    offset = (page - 1) * size
    total = Post.objects.count()

    if total == 0:
        return 200, {
            "posts": [],
            "pagination": {
                "total": total,
                "page": page,
                "size": size,
            },
        }

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


@router.get("/ids", response=IdsSchema)
def get_all_post_ids(request):
    # QuerySet的values_list()方法与values类似
    # 不过返回的是一个元组而非字典
    # flat可以使返回一个值时返回那个值而非一个一元组
    # print(Post.objects.values_list("id", flat=True))
    return {"ids": list(Post.objects.values_list("id", flat=True))}


@router.get("/sitemap", response={200: PostIdsForSitemap})
def get_all_post_ids_for_sitemap(request):
    posts = Post.objects.values("id", "slug", "content_update_at")
    # transform to Pydantic model
    post_schemas = [PostSitemapSchema(**post) for post in posts]
    return 200, PostIdsForSitemap(root=post_schemas)


# TODO: 优化这里, 准确率太低了.
@router.get(
    "/search",
    response={
        200: PostCardsWithSimilaritySchema,
        400: MessageSchema,
        429: MessageSchema,
    },
)
@rate_limit(key_prefix="post_search", max_requests=10, window=1)
def get_post_cards_from_query(
    request,
    q: str,
    page: PositiveInt = 1,
    size: PositiveInt = 10,
):
    # cache
    cache_key = f"post_search_results:{hash(q)}"
    cached = cache.get(cache_key)

    # length limit
    if len(q) > 200:
        return 400, {"message": "Query too long"}

    # find cache
    if cached is None:
        task = generate_search_embedding_task.delay(q)
        query_embedding = task.get(timeout=1)

        post_query = (
            Post.objects.annotate(
                similarity=CosineDistance("embedding", query_embedding)
            )
            .filter(similarity__lt=CONFIDENCE)
            .order_by("similarity")
            .values_list("id", "similarity")
        )
        result = list(post_query)
        cache.set(cache_key, result, timeout=3600)  # 1h
    else:
        result = cached

    # paginate
    total = len(result)
    offset = (page - 1) * size
    paginated_result = result[offset : offset + size]

    # if empty
    if not paginated_result:
        return 200, {
            "posts_with_similarity": [],
            "pagination": {"total": total, "page": page, "size": size},
        }

    # Assemble into corresponding structure
    paginated_ids = [item[0] for item in paginated_result]
    # Replace in_bulk with filter + select_related + prefetch_related to avoid N+1 queries
    posts_dict = (
        Post.objects.select_related("category")
        .prefetch_related("tags")
        .in_bulk(paginated_ids)
    )

    posts_with_similarity = []
    for post_id, similarity in paginated_result:
        post_obj = posts_dict.get(post_id)
        if post_obj:
            posts_with_similarity.append({"post": post_obj, "similarity": similarity})

    return 200, {
        "posts_with_similarity": posts_with_similarity,
        "pagination": {"total": total, "page": page, "size": size},
    }


@router.get(
    "/{int:post_id}",
    response={200: PostsSchema, 404: MessageSchema, 500: MessageSchema},
)
def get_post(request, post_id: int):
    try:
        post = Post.objects.get(pk=post_id)
        return post
    except Post.DoesNotExist:
        return 404, {"message": "Not found"}
    except Exception as e:
        logging.error(e)
        return 500, {"message": "Internal Server Error"}


# NOTE:
# must put dynamic routing under static routing
# if add new static router remember to add the name to exclude list manually
# at 'api/admin.py' and 'api/models.py'
@router.get(
    "/{str:post_slug}",
    response={200: PostsSchema, 404: MessageSchema, 500: MessageSchema},
)
def get_post_from_slug(request, post_slug: str):
    try:
        post = Post.objects.get(slug=post_slug)
        return post
    except Post.DoesNotExist:
        return 404, {"message": "Not found"}
    except Exception as e:
        logging.error(e)
        return 500, {"message": "Internal Server Error"}
