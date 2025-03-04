from ninja import Router

from api.auth import TimeBaseAuth
from api.models import Author, Category, Comment, Guest, Post, Tag
from api.schemas import (
    GuestLoginSchema,
    IdSchema,
    MessageSchema,
    NewCommentSchema,
    RenderSchema,
)

router = Router()


@router.get("/test", auth=TimeBaseAuth())
def front_server_api(request):
    return {"status": "authenticated"}


@router.post("/guest/login", auth=TimeBaseAuth(), response=IdSchema)
def guest_login(request, body: GuestLoginSchema):
    guest, created = Guest.objects.get_or_create(
        name=body.name,
        unique_id=f"{body.provider}-{body.provider_id}",
    )
    return guest


@router.post("/comment/new", auth=TimeBaseAuth(), response=MessageSchema)
def new_comment(request, body: NewCommentSchema):
    try:
        post = Post.objects.get(pk=body.post_id)
        guest = Guest.objects.get(unique_id=body.unique_id)

        Comment.objects.create(content=body.content, post=post, guest=guest)
        return 200, {"message": "Comment created successfully"}
    except Post.DoesNotExist:
        return 404, {"message": "Post not found"}
    except Guest.DoesNotExist:
        return 404, {"message": "Guest not found"}


@router.post("/render", auth=TimeBaseAuth())
def render(request, body: RenderSchema):
    post = Post.objects.get(pk=body.id)
    fields = body.dict(exclude={"id"})
    # print(fields)

    if fields.get("content_html") is not None:
        post.content_html = fields.get("content_html")

    if fields.get("cover_image") is not None:
        post.cover_image = fields.get("cover_image")

    if fields.get("header_image") is not None:
        post.header_image = fields.get("header_image")

    if fields.get("slug") is not None:
        post.slug = fields.get("slug")

    if fields.get("meta_description") is not None:
        post.meta_description = fields.get("meta_description")

    # 改为便捷的get_or_create()
    # 处理作者
    if fields.get("author") is not None:
        author_name = fields.get("author")
        author, author_created = Author.objects.get_or_create(name=author_name)
        post.author = author

    # 处理分类
    if fields.get("category") is not None:
        category_name = fields.get("category")
        category, category_created = Category.objects.get_or_create(name=category_name)
        post.category = category

    # 处理标签
    if fields.get("tags") is not None:
        new_tags = []
        name_of_tags = fields.get("tags", [])
        for tag_name in name_of_tags:
            new_tag, tags_created = Tag.objects.get_or_create(name=tag_name)
            new_tags.append(new_tag)
        post.tags.set(new_tags)

    post.save()
