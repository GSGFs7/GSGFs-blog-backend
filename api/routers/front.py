from ninja import Router

from api.auth import TimeBaseAuth
from api.models import Author, Category, Comment, Guest, Post, Tag
from api.schemas import (
    GuestLoginSchema,
    IdSchema,
    MessageSchema,
    NewCommentSchema,
    RenderSchema,
    GuestSchema,
)

router = Router(auth=TimeBaseAuth())


@router.get("/test")
def front_server_api(request):
    return {"status": "authenticated"}


@router.post("/guest/login", response=IdSchema)
def guest_login(request, body: GuestLoginSchema):
    try:
        guest = Guest.objects.get(unique_id=f"{body.provider}-{body.provider_id}")

        guest.avatar = body.avatar_url
        guest.name = body.name
        guest.save()
    except:
        guest = Guest.objects.create(
            unique_id=f"{body.provider}-{body.provider_id}",
            provider=body.provider,
            provider_id=body.provider_id,
            name=body.name,
            avatar=body.avatar_url,
        )
    return guest


@router.get("/guest/{int:guest_id}", response={200: GuestSchema, 404: MessageSchema})
def get_guest(request, guest_id: int):
    try:
        guest = Guest.objects.get(pk=guest_id)
        return guest
    except:
        return 404, {"message": "Not found"}


@router.post("/comment/new", response={200: IdSchema, 404: MessageSchema})
def new_comment(request, body: NewCommentSchema):
    try:
        post = Post.objects.get(pk=body.post_id)
        guest = Guest.objects.get(unique_id=body.unique_id)

        comment = Comment.objects.create(content=body.content, post=post, guest=guest)
        comment.OS = body.metadata.OS
        comment.user_agent = body.metadata.user_agent
        comment.browser = body.metadata.browser
        comment.browser_version = body.metadata.browser_version
        comment.platform = body.metadata.platform
        comment.save()

        return 200, {"id": comment.id}
    except Post.DoesNotExist:
        return 404, {"message": "Post not found"}
    except Guest.DoesNotExist:
        return 404, {"message": "Guest not found"}


@router.post("/render")
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
