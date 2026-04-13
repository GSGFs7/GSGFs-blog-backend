from django.db import models

from .base import BaseModel


class Gal(BaseModel):
    vndb_id = models.CharField(
        blank=False, max_length=10, unique=True, help_text="在VNDB中的ID, 必填"
    )
    title = models.CharField(max_length=100, null=True, blank=True)
    title_cn = models.CharField(max_length=100, null=True, blank=True)

    # score
    character_score = models.FloatField(blank=True, null=True)
    story_score = models.FloatField(blank=True, null=True)
    comprehensive_score = models.FloatField(blank=True, null=True)
    vndb_rating = models.FloatField(blank=True, null=True)

    # review
    summary = models.CharField(
        max_length=200, blank=True, null=True, help_text="显示在外面, 类似于备注"
    )  # No spoilers
    review = models.TextField(blank=True, null=True)
    review_html = models.TextField(blank=True, null=True)

    cover_image = models.URLField(
        max_length=500, blank=True, null=True, help_text="(暂时没用)"
    )

    def __str__(self):
        return self.vndb_id

    def save(self, *args, **kwargs) -> None:
        return super().save(*args, **kwargs)
