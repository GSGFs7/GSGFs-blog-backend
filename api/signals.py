from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Gal, Page, Post
from .utils import extract_keywords
from .vndb import query_vn


@receiver(pre_save, sender=Post)
@receiver(pre_save, sender=Page)
def add_keywords(sender, instance, **kwargs):
    if not instance.keywords:
        instance.keywords = extract_keywords(instance.content)


@receiver(pre_save, sender=Gal)
def sync_with_vndb(sender, instance, **kwargs):
    def find_cn_title(titles):
        for title in titles:
            if title["lang"] == "zh-Hans":
                return title["title"]
        return None

    if not instance.vndb_id:
        return

    if not instance.pk or not instance.title:
        try:
            # circular import, must use signals to avoid
            res = query_vn(instance.vndb_id)
            if not res["results"]:
                return

            vn_data = res["results"][0]

            # Update the instance not the database directly
            instance.title = vn_data.get("alttitle", vn_data["title"])
            instance.title_cn = find_cn_title(vn_data.get("titles", []))
            instance.cover_image = vn_data["image"]["url"]
            instance.vndb_rating = vn_data.get("rating", None)
            # This is a pre_save signal, should not call `save()` here otherwise it will cause infinite loop
        except:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"更新 VNDB 数据失败: {instance.vndb_id}")
