import logging

from celery import shared_task

from .models import Gal
from .nvdb import query_vn

logger = logging.getLogger(__name__)


@shared_task
def sync_vndb_data():
    """
    Celery task to synchronize VNDB data.
    """
    logger.info("开始同步 VNDB 数据...")
    entries = Gal.objects.all()

    for entry in entries:
        try:
            data = query_vn(entry.vndb_id)

            if "results" in data and data["results"]:
                vn_data = data["results"][0]

                entry.title = vn_data.get("alttile", vn_data["title"])
                title_cn = None
                for title in vn_data.get("titles", []):
                    if title["lang"] == "zh-Hans":
                        title_cn = title["title"]
                        break
                entry.title_cn = title_cn
                entry.cover_image = vn_data["image"]["url"]
                entry.vndb_rating = vn_data.get("rating", None)

                entry.save()
            else:
                logger.warning(f"未找到 VNDB 数据: {entry.vndb_id}")
                continue
        except Exception as e:
            logger.error(f"查询 VNDB 数据失败: {entry.vndb_id}, 错误: {e}")
            continue
    logger.info("VNDB 数据同步完成。")
