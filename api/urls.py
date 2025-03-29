# import base64
# import datetime
# import hashlib
# import hmac
# import math
# import random
# import time
# from typing import Annotated, Generic, List, Optional, TypeVar

# import jwt
# from django.conf import settings
# from django.contrib.auth import authenticate
# from django.db import models
# from django.http import HttpResponse
# from django.shortcuts import get_object_or_404
# from django.utils import timezone
# from ninja import Form, NinjaAPI, Path, Router, Schema
# from ninja.responses import codes_4xx
# from ninja.security import APIKeyHeader, HttpBearer, django_auth
# from pydantic import PositiveInt, WrapValidator
# from pydantic_core import PydanticUseDefault

# from .auth import TimeBaseAuth
# from .models import Author, Category, Comment, Guest, Post, Tag
# from .schemas import (
#     CategoryResponseSchema,
#     CommentIdsSchema,
#     CommentSchema,
#     GuestLoginSchema,
#     GuestSchema,
#     IdSchema,
#     LoginSchema,
#     MessageSchema,
#     NewCommentSchema,
#     PostIdsForSitemap,
#     PostsCardsSchema,
#     PostsSchema,
#     RenderSchema,
#     TokenSchema,
# )

from ninja import NinjaAPI

from .routers.categories import router as categories_router
from .routers.comments import router as comment_router
from .routers.front import router as front_router
from .routers.gal import router as gal_router
from .routers.posts import router as posts_router

api = NinjaAPI()

api.add_router("/category", categories_router)
api.add_router("/comment", comment_router)
api.add_router("/front", front_router)
api.add_router("/gal", gal_router)
api.add_router("/post", posts_router)
