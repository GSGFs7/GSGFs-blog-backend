from django.db import models

from .base import BaseModel


class Anime(BaseModel):
    mal_id = models.IntegerField(blank=False, help_text="在MyAnimeList中的ID, 必填")
    name = models.CharField(
        max_length=100, blank=True, null=False, unique=True, db_index=True
    )
    name_cn = models.CharField(max_length=100, blank=True, null=True)
    year = models.IntegerField(default=None, blank=True, null=True)
    synopsis = models.TextField(default=None, blank=True, null=True)
    cover_image = models.URLField(max_length=500, blank=True, null=True)
    # https://en.wikipedia.org/wiki/Motion_Picture_Association_film_rating_system
    rating = models.CharField(blank=True, null=True)

    # fill it by your self
    score = models.FloatField(blank=True, null=True)
    review = models.TextField(blank=True, null=True)

    class Meta(BaseModel.Meta):
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
