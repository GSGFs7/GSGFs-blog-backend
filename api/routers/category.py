from ninja import Router
from pydantic import PositiveInt

from api.models import Category, Post
from api.schemas import CategoryResponseSchema, MessageSchema

router = Router()


@router.get(
    "/{int:category_id}",
    response={200: CategoryResponseSchema, 400: MessageSchema, 404: MessageSchema},
)
def category_get_post(
    request, category_id: int, page: PositiveInt = 1, size: PositiveInt = 10
):
    try:
        category = Category.objects.get(pk=category_id)
        posts = Post.objects.filter(category=category)

        offset = (page - 1) * size
        total = posts.count()

        if offset >= total:
            return 400, {"message": "Out of range"}

        return 200, {
            "posts": list(posts),
            "pagination": {
                "total": total,
                "page": page,
                "size": size,
            },
            "name": category.name,
        }
    except Category.DoesNotExist:
        return 404, {"message": f"Category 'id={category_id}' not found"}
