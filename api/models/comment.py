from django.db import models

from .base import BaseModel
from .guest import Guest
from .post import Post


class Comment(BaseModel):
    content = models.TextField(max_length=10000)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name="comments")

    # 用户信息
    user_agent = models.CharField(max_length=100, blank=True, default="unknown")
    OS = models.CharField(max_length=100, blank=True, default="unknown")
    platform = models.CharField(max_length=100, blank=True, default="unknown")
    browser = models.CharField(max_length=100, blank=True, default="unknown")
    browser_version = models.CharField(max_length=100, blank=True, default="unknown")

    def __str__(self):
        return self.content[:10]
