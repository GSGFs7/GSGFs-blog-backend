from ninja import Router

from api.schemas import CommentSchema, MessageSchema, CommentIdsSchema
from api.models import Comment, Post

router = Router()


# 从id获取评论
@router.get(
    "/{int:comment_id}", response={200: CommentSchema, 404: MessageSchema}
)
def get_comment(request, comment_id: int):
    try:
        comment = Comment.objects.select_related("guest").get(pk=comment_id)
        return comment
    except:
        return {"message": "Not found"}


# 从文章获取评论id
@router.get(
    "/post/{int:post_id}",
    response={200: CommentIdsSchema, 404: MessageSchema},
)
def get_comment_from_post(request, post_id: int):
    try:
        post = Post.objects.get(pk=post_id)
        comments = post.comment.all()
        return 200, {"ids": [i.id for i in comments]}
    except Post.DoesNotExist:
        return 404, {"message": "Post not found"}
