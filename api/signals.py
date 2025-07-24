import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .jikan import query_anime
from .markdown import markdown_to_html_frontend
from .models import Anime, Gal, Post
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
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"更新 VNDB 数据失败({instance.vndb_id}): {e}")


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
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"更新 Anime 数据失败({instance.mal_id}): {e}")


@receiver(post_save, sender=Gal)
def convert_gal_markdown_to_html(sender, instance, **kwargs):
    try:
        res = markdown_to_html_frontend(instance.review)
        instance.review_html = res.html
        instance.save(update_fields=["review_html"])
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Markdown 转换失败: {e}")


@receiver(post_save, sender=Post)
def convert_post_markdown_to_html(sender, instance, **kwargs):
    try:
        res = markdown_to_html_frontend(instance.content)
        instance.content_html = res.html
        instance.save(update_fields=["content_html"])
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Markdown 转换失败: {e}")
