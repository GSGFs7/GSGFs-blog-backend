from django.db import models

from .base import BaseModel


class Guest(BaseModel):
    class Providers(models.TextChoices):
        github = "github", "github"
        google = "google", "google"
        myself = "myself", "myself"
        osu = "osu", "osu"

    name = models.CharField(max_length=50)
    # unique_id 就是 "provider" + "-" + "provider_id"
    unique_id = models.CharField(max_length=50, unique=True, db_index=True)  # 添加索引
    email = models.EmailField()
    password = models.CharField(max_length=128)
    provider = models.CharField(
        max_length=10, choices=Providers, default=Providers.myself
    )
    provider_id = models.IntegerField()
    avatar = models.URLField(max_length=200)
    is_admin = models.BooleanField(default=False)
    last_visit = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
