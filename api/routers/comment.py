from django.core.mail import mail_admins
from ninja import Router

from api.auth import TimeBaseAuth
from api.models import Comment, Guest, Post
from api.schemas import (
    CommentIdsSchema,
    CommentSchema,
    IdSchema,
    MessageSchema,
    NewCommentSchema,
)

router = Router()


# 从id获取评论
@router.get("/{int:comment_id}", response={200: CommentSchema, 404: MessageSchema})
def get_comment(request, comment_id: int):
    try:
        comment = Comment.objects.select_related("guest").get(pk=comment_id)
        return comment
    except:
        return 404, {"message": "Not found"}


# 从文章获取评论id
@router.get(
    "/post/{int:post_id}",
    response={200: CommentIdsSchema, 404: MessageSchema},
)
def get_comment_from_post(request, post_id: int):
    try:
        post = Post.objects.get(pk=post_id)
        comments = post.comment.all()  # type: ignore
        return 200, {"ids": [i.id for i in comments]}
    except Post.DoesNotExist:
        return 404, {"message": "Post not found"}


@router.post(
    "/new",
    response={200: IdSchema, 404: MessageSchema},
    auth=TimeBaseAuth(),
)
def new_comment(request, body: NewCommentSchema):
    try:
        post = Post.objects.get(pk=body.post_id)
        guest = Guest.objects.get(unique_id=body.unique_id)

        comment = Comment.objects.create(content=body.content, post=post, guest=guest)
        if not body.metadata is None:
            comment.OS = body.metadata.OS
            comment.user_agent = body.metadata.user_agent
            comment.browser = body.metadata.browser
            comment.browser_version = body.metadata.browser_version
            comment.platform = body.metadata.platform
            comment.save()

        # tall admin had a new comment
        # mail_admins("had a new comment", f"had a new comment in post '{post.title}'")  # too slow

        return 200, {"id": comment.pk}  # pk = id
    except Post.DoesNotExist:
        return 404, {"message": "Post not found"}
    except Guest.DoesNotExist:
        return 404, {"message": "Guest not found"}
