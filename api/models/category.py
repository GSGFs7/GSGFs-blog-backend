from django.db import models

from .base import BaseModel


class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True, db_index=True, null=False)

    def __str__(self):
        return self.name
