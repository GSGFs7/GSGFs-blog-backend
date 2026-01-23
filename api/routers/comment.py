import logging

from ninja import Router

from api.auth import TimeBaseAuth
from api.models import Comment, Guest, Post
from api.schemas import (
    CommentIdsSchema,
    CommentResponse,
    CommentSchema,
    IdSchema,
    MessageSchema,
    NewCommentSchema,
)
from api.tasks import mail_admins_task

router = Router()


# 从id获取评论
@router.get(
    "/{int:comment_id}",
    response={200: CommentSchema, 404: MessageSchema, 500: MessageSchema},
)
def get_comment(request, comment_id: int):
    try:
        comment = Comment.objects.select_related("guest").get(pk=comment_id)
        return comment
    except Comment.DoesNotExist:
        return 404, {"message": "Not found"}
    except Exception as e:
        logging.error(e)
        return 500, {"message": "Internal Server Error"}


# 从文章获取评论id
@router.get(
    "/post/{int:post_id}",
    response={200: CommentIdsSchema, 404: MessageSchema, 500: MessageSchema},
)
def get_comment_from_post(request, post_id: int):
    try:
        post = Post.objects.get(pk=post_id)
        comments = post.comments.all()  # type: ignore
        return 200, {"ids": [i.id for i in comments]}
    except Post.DoesNotExist:
        return 404, {"message": "Not found"}
    except Exception as e:
        logging.error(e)
        return 500, {"message": "Internal Server Error"}


# get all comment with content
@router.get(
    "/post/{int:post_id}/all",
    response={200: CommentResponse, 404: MessageSchema, 500: MessageSchema},
)
def get_all_comment_from_post(request, post_id: int):
    try:
        post = Post.objects.get(pk=post_id)
        comments = post.comments.select_related("guest").all()  # type: ignore
        return 200, {"comments": list(comments)}
    except Post.DoesNotExist:
        return 404, {"message": "Not found"}
    except Exception as e:
        logging.error(e)
        return 500, {"message": "Internal Server Error"}


@router.post(
    "/new",
    response={200: IdSchema, 404: MessageSchema, 500: MessageSchema},
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
        mail_admins_task.delay(
            "had a new comment", f"had a new comment in post '{post.title}'"
        )

        return 200, {"id": comment.pk}  # pk = id
    except Post.DoesNotExist:
        return 404, {"message": "Post not found"}
    except Guest.DoesNotExist:
        return 404, {"message": "Guest not found"}
    except Exception as e:
        logging.error(e)
        return 500, {"message", "Internal Server Error"}
