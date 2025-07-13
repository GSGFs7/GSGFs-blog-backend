from django.db.models.signals import pre_save
from django.dispatch import receiver

from .jikan import query_anime
from .models import Anime, Gal
from .vndb import query_vn


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


@receiver(pre_save, sender=Anime)
def sync_with_jikan(sender, instance, **kwargs):
    if not instance.mal_id:
        return

    if not instance.pk or not instance.title:
        try:
            res = query_anime(instance.mal_id)

            title = None
            for t in res.titles:
                if t.type == "Japanese":
                    title = t.title
            if title is None:
                title = res.titles[0].title

            instance.name = title
            instance.year = res.year
            instance.synopsis = res.synopsis
            instance.cover_image = res.images.webp.large_image_url
            instance.rating = res.rating
        except:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"更新 Anime 数据失败: {instance.mal_id}")
