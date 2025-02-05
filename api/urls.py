import base64
import datetime
import hashlib
import hmac
import math
import random
import time
from typing import Annotated, Generic, List, Optional, TypeVar

import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.db import models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Form, NinjaAPI, Path, Router, Schema
from ninja.responses import codes_4xx
from ninja.security import APIKeyHeader, HttpBearer, django_auth
from pydantic import PositiveInt, WrapValidator
from pydantic_core import PydanticUseDefault

from .auth import TimeBaseAuth
from .models import Author, Category, Guest, Post, Tag
from .schemas import (
    LoginSchema,
    MessageSchema,
    PostsCardsSchema,
    PostsSchema,
    TokenSchema,
    renderSchema,
    CategoryResponseSchema,
)

api = NinjaAPI()


@api.get("/posts", response={200: PostsCardsSchema, 400: MessageSchema})
def get_posts(request, page: PositiveInt = 1, size: PositiveInt = 10):
    offset = (page - 1) * size  # 起点
    total = Post.objects.count()

    if offset >= total:
        return 400, {"message": "Out of range"}

    posts = Post.objects.all().filter(is_deleted=False)[offset : offset + size]
    return 200, {
        "posts": list(posts),
        "pagination": {
            "total": total,  # 一共有多少个
            "page": page,  # 当前是第几页
            "size": size,  # 一页的数量
        },
    }


@api.get("/posts/ids")
def get_all_post_ids(request):
    # QuerySet的values_list()方法与values类似
    # 不过返回的是一个元组而非字典
    # flat可以使返回一个值时返回那个值而非一元组
    # print(Post.objects.values_list("id", flat=True))
    return {"ids": list(Post.objects.values_list("id", flat=True))}


@api.get("/post/{int:post_id}", response=PostsSchema)
def get_post(request, post_id: int):
    post = Post.objects.get(pk=post_id)
    return post

@api.get("/post/")


@api.get(
    "/category/{int:category_id}",
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


@api.post("/login", response=TokenSchema)
def login(request, payload: LoginSchema):
    def create_token(user):
        exp = datetime.datetime.now() + datetime.timedelta(days=1)
        return jwt.encode(
            {"user_id": user.id, "exp": exp}, "secret-key", algorithm="HS256"
        )

    # user = authenticate(username=payload.username, password=payload.password)
    guest = None

    try:
        guest = Guest.objects.get(email=payload.email, provider=payload.provider)
    except Guest.DoesNotExist:
        return api.create_response(
            request, {"detail": "Invalid credentials"}, status=401
        )

    if guest.password != payload.password:
        return api.create_response(
            request, {"detail": "Invalid credentials"}, status=401
        )

    token = create_token(guest)
    return {"access_token": token}


@api.post("/auth/callback")
def auth_callback(request):
    data = request.POST

    # guest


@api.get("/front-server-api/test", auth=TimeBaseAuth())
def front_server_api(request):
    return {"status": "authenticated"}


@api.post("/front-server-api/render", auth=TimeBaseAuth())
def render(request, body: renderSchema):
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

    # try:
    #     Author.objects.get(name=fields.get("author"))
    # except Author.DoesNotExist:
    #     new_author = Author(name=fields.get("author"))
    #     new_author.save()
    # post.author = Author.objects.get(name=fields.get("author"))

    # try:
    #     Category.objects.get(name=fields.get("category"))
    # except Category.DoesNotExist:
    #     new_category = Category(name=fields.get("category"))
    #     new_category.save()
    # post.category = Category.objects.get(name=fields.get("category"))

    # new_tags = []
    # for tag in fields.get("tags"):
    #     try:
    #         Tag.objects.get(tag)
    #     except Tag.DoesNotExist:
    #         new_tag = Tag(name=tag)
    #         new_tag.save()
    #     new_tags.append(Tag.objects.get(name=tag))
    # post.tags = new_tags

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
