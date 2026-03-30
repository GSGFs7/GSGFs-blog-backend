import logging
from io import BytesIO

from celery import shared_task
from django.core.files.base import ContentFile
from django.core.mail import mail_admins
from django.db import transaction
from django.utils import timezone
from PIL import Image as PILImage

from .ml_model import get_sentence_transformer_model
from .models import Gal, ImageResource, Post, PostChunk
from .utils import chunk_text
from .vndb import query_vn

logger = logging.getLogger(__name__)


UPDATE_VNDB_INTERVAL: int = 60 * 60 * 24 * 7  # Updated every 7 days


# TODO: updated field configable
@shared_task
def sync_vndb_data():
    """
    Celery task to synchronize VNDB data.
    """
    logger.info("开始同步 VNDB 数据...")
    entries = Gal.objects.all()
    current_time = timezone.now().timestamp()

    for entry in entries:
        if current_time - entry.updated_at.timestamp() < UPDATE_VNDB_INTERVAL:
            logger.info(f"跳过最近已更新: {entry.vndb_id}")
            continue

        try:
            data = query_vn(entry.vndb_id)

            if "results" in data and data["results"]:
                vn_data = data["results"][0]
                # alt_title = vn_data.get("alttitle", None)
                # if alt_title and isinstance(alt_title, str) and alt_title.strip():
                #     entry.title = alt_title
                # else:
                #     entry.title = vn_data["title"]
                # title_cn = None
                # for title in vn_data.get("titles", []):
                #     if title["lang"] == "zh-Hans":
                #         title_cn = title["title"]
                #         break
                # entry.title_cn = title_cn
                # entry.cover_image = vn_data["image"]["url"]
                entry.vndb_rating = vn_data.get("rating", None)  # rating only

                entry.save()
            else:
                logger.warning(f"未找到 VNDB 数据: {entry.vndb_id}")
                continue
        except Exception as e:
            logger.error(f"查询 VNDB 数据失败: {entry.vndb_id}, 错误: {e}")
            continue
    logger.info("VNDB 数据同步完成。")


@shared_task
def mail_admins_task(subject: str, message: str):
    try:
        mail_admins(subject, message)
        logging.info("Success mail admin")
    except Exception as e:
        logging.warning(f"Mail admin failed: {e}")


@shared_task
@transaction.atomic
def generate_post_chunks_embedding_task(post_id: int):
    post = Post.objects.get(id=post_id)
    model = get_sentence_transformer_model()

    # clean old chunk
    post.chunks.all().delete()

    text_chunk = chunk_text(post.content)

    new_chunks = []
    for i, content in enumerate(text_chunk):
        vector = model.encode_document(content)
        new_chunks.append(
            PostChunk(
                post=post,
                content=content,
                embedding=vector,
                chunk_index=i,
            )
        )

    PostChunk.objects.bulk_create(new_chunks)


@shared_task
def generate_search_embedding_task(query: str):
    """
    Celery task to generate embedding for search query.
    """
    try:
        model = get_sentence_transformer_model()
        embedding = model.encode_query(query)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"生成搜索 embedding 失败: {query[:50]}, 错误: {e}")
        raise


@shared_task
def process_image(image_resource_id: int):
    """
    Generate optimized versions (WebP, AVIF) and thumbnail for an image.
    """
    try:
        image_res_obj = ImageResource.objects.get(id=image_resource_id)

        if image_res_obj.is_processed:
            return

        with PILImage.open(image_res_obj.file) as img:
            # AVIF
            if not image_res_obj.avif_file:
                try:
                    buffer = BytesIO()  # in memory
                    img.save(buffer, format="AVIF", quality=80)

                    data = buffer.getvalue()
                    # filename also use raw image check sum
                    filename = f"{image_res_obj.checksum}.avif"

                    image_res_obj.avif_file.save(
                        filename, ContentFile(data), save=False
                    )

                    logger.info(f"Successfully generated AVIF for {image_resource_id}")
                except Exception as e:
                    logger.warning(
                        f"Could not generate AVIF for {image_resource_id}: {e}"
                    )

            # WebP
            if not image_res_obj.webp_file:
                try:
                    buffer = BytesIO()
                    img.save(buffer, format="WEBP", quality=80)

                    data = buffer.getvalue()
                    filename = f"{image_res_obj.checksum}.webp"

                    image_res_obj.webp_file.save(
                        filename, ContentFile(data), save=False
                    )

                    logger.info(f"Successfully generated WebP for {image_resource_id}")
                except Exception as e:
                    logger.warning(
                        f"Could not generate WebP for {image_resource_id}: {e}"
                    )

            # Thumbnail, AVIF default
            if not image_res_obj.thumbnail:
                try:
                    thumb_img = img.copy()
                    thumb_img.thumbnail((300, 300))

                    buffer = BytesIO()
                    thumb_img.save(buffer, format="AVIF", quality=60)
                    data = buffer.getvalue()
                    filename = f"{image_res_obj.checksum}_thumb.avif"

                    image_res_obj.thumbnail.save(
                        filename, ContentFile(data), save=False
                    )

                    logger.info(
                        f"Successfully generated thumbnail for {image_resource_id}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to generate thumbnail for {image_resource_id}: {e}"
                    )

            image_res_obj.is_processed = True
            image_res_obj.save()
    except ImageResource.DoesNotExist:
        logger.error(f"Image not found: {image_resource_id}")
    except Exception as e:
        logger.error(f"Error processing image {image_resource_id}: {e}")
