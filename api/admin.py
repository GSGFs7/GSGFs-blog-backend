from io import BytesIO

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from api.constants import IMAGE_ALLOWED_FORMAT, POST_RESERVED_SLUGS
from api.models import (
    Anime,
    Comment,
    Gal,
    Guest,
    Image,
    Post,
    Tag,
)
from api.utils import chinese_slugify, extract_metadata


class ImageAdminForm(forms.ModelForm):
    file = forms.ImageField(required=True, label="image")

    class Meta:
        model = Image
        fields = ["original_name", "alt_text", "description", "uploaded_by"]
        help_texts = {
            "checksum": "blake3 算法得到的哈希值",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk is None:
            self.fields["file"] = forms.ImageField(required=True, label="image")
        else:
            if "file" in self.fields:
                del self.fields["file"]

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if not file:
            return file

        if file.content_type not in IMAGE_ALLOWED_FORMAT:
            raise ValidationError(
                f"Not allowed format: {file.content_type}. "
                f"Allowed format: {', '.join(IMAGE_ALLOWED_FORMAT)}"
            )
        return file

    def save(self, commit=True):
        # Call super().save(commit=False) to ensure self.save_m2m is initialized by Django
        instance = super().save(commit=False)
        file = self.cleaned_data.get("file")

        if file:
            file.seek(0)
            content = BytesIO(file.read())
            img, _ = Image.create_from_file(content, file.name)

            img.original_name = self.cleaned_data.get("original_name") or file.name
            img.alt_text = self.cleaned_data.get("alt_text", "")
            img.description = self.cleaned_data.get("description", "")
            img.uploaded_by = self.cleaned_data.get("uploaded_by")

            if commit:
                img.save()

            return img

        if commit:
            instance.save()
            # self.save_m2m()

        return instance


class ImageAdmin(admin.ModelAdmin):
    form = ImageAdminForm
    readonly_fields = [
        "preview_large",
        "resource_info",
        "mime_type",
        "size",
        "size_formatted",
        "width",
        "height",
        "checksum",
        "created_at",
        "updated_at",
        "id",
        "width_px",
        "height_px",
    ]

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            # new
            return [
                (
                    None,
                    {
                        "fields": [
                            "file",
                            "preview_large",
                            "original_name",
                            "alt_text",
                            "description",
                        ]
                    },
                ),
                (
                    "upload info",
                    {
                        "fields": [
                            "uploaded_by",
                            "created_at",
                            "updated_at",
                        ]
                    },
                ),
            ]
        else:
            # edit
            return [
                (
                    None,
                    {
                        "fields": [
                            "id",
                            "preview_large",
                            "original_name",
                            "alt_text",
                            "description",
                        ]
                    },
                ),
                (
                    "resource info",
                    {
                        "fields": [
                            "resource_info",
                            "mime_type",
                            "size_formatted",
                            "width_px",
                            "height_px",
                            "checksum",
                        ],
                    },
                ),
                (
                    "upload info",
                    {
                        "fields": [
                            "uploaded_by",
                            "created_at",
                            "updated_at",
                        ]
                    },
                ),
            ]

    list_display = [
        "original_name",
        "preview_icon",
        "mime_type",
        "size_formatted",
        "created_at",
    ]
    list_filter = ["created_at"]
    search_fields = ["original_name", "alt_text", "description"]
    date_hierarchy = "created_at"

    @admin.display(description="size")
    def size_formatted(self, obj: Image):
        size = obj.resource.size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KiB"
        else:
            return f"{size / (1024 * 1024):.1f} MiB"

    @admin.display(description="thumbnail")
    def preview_icon(self, obj: Image):
        if obj.resource and obj.resource.file:
            return mark_safe(
                f'<img src="{
                    obj.resource.thumbnail.url
                    if obj.resource.thumbnail
                    else obj.resource.file.url
                }"'
                f' height="100px"'
                f' style="width: auto; max-width: 100%; object-fit: contain;"'
                f"/>"
            )
        return "no img"

    @admin.display(description="image preview")
    def preview_large(self, obj: Image):
        if obj.resource and obj.resource.file:
            return mark_safe(
                f'<img src="{
                    obj.resource.thumbnail.url
                    if obj.resource.thumbnail
                    else obj.resource.file.url
                }"'
                f' style="max-width: 300px; max-height: 300px;"'
                f"/>"
            )
        return "no img"

    @admin.display(description="resource info")
    def resource_info(self, obj: Image):
        if obj.resource:
            return f"ID: {obj.resource.id}"
        return "no resource"

    @admin.display(description="MIME type")
    def mime_type(self, obj: Image):
        return obj.resource.mime_type if obj.resource else "-"

    @admin.display(description="width")
    def width(self, obj: Image):
        return obj.resource.width if obj.resource else "-"

    @admin.display(description="height")
    def height(self, obj: Image):
        return obj.resource.height if obj.resource else "-"

    @admin.display(description="checksum")
    def checksum(self, obj: Image):
        return obj.resource.checksum if obj.resource else "-"

    @admin.display(description="size")
    def size(self, obj: Image):
        return obj.resource.size if obj.resource else 0

    @admin.display(description="width")
    def width_px(self, obj: Image):
        return f"{obj.resource.width} px"

    @admin.display(description="height")
    def height_px(self, obj: Image):
        return f"{obj.resource.width} px"


class PostAdminForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = "__all__"

    def clean(self):
        """
        Cleans and validates form data for a Post model.

        - Extracts metadata from the 'content' field using front matter if available.
        - If 'title' is missing, attempts to extract it from metadata;
         checks for uniqueness.
        - Automatically generates 'slug' from metadata or the title if not provided.
        - Collects validation errors for missing or duplicate fields and raises
         ValidationError if any are found.

        Returns:
            dict: The cleaned and possibly modified form data.

        Raises:
            ValidationError: If required fields are missing, cannot be
            extracted/generated, or if the title is not unique.
        """

        cleaned_data = super().clean()
        title = cleaned_data.get("title")
        content = cleaned_data.get("content")

        metadata = {}
        errors = {}

        # === content ===
        if content:
            metadata = extract_metadata(content)
        else:
            errors["content"] = "Content field cannot be empty."

        # === tags ===
        if not cleaned_data.get("tags"):
            tag_names = metadata.get("tags")
            if tag_names:
                tags_to_set = []
                for tag_name in tag_names:
                    tag_obj, _ = Tag.objects.get_or_create(name=tag_name)
                    tags_to_set.append(tag_obj)
                cleaned_data["tags"] = tags_to_set

        # === title ===
        if not title:
            extracted_title = metadata.get("title")
            if extracted_title:
                cleaned_data["title"] = extracted_title
                if (
                    Post.objects.filter(title=extracted_title)
                    .exclude(pk=self.instance.pk)
                    .exists()
                ):
                    errors["title"] = (
                        "The title extracted from Front Matter already exists."
                    )
            else:
                errors["title"] = (
                    "The title field cannot be empty and cannot be "
                    "automatically extracted from Front Matter."
                )

        # === slug ===
        if not cleaned_data.get("slug"):
            cleaned_data["slug"] = metadata.get("slug") or chinese_slugify(
                str(cleaned_data.get("title", ""))
            )
            if not cleaned_data.get("slug"):
                errors["slug"] = (
                    "Slug field cannot be empty and cannot be automatically generated."
                )
            if (
                Post.objects.filter(slug=cleaned_data.get("slug"))
                .exclude(pk=self.instance.pk)
                .exists()
            ):
                errors["slug"] = "The slug already exists."
        if cleaned_data.get("slug") in POST_RESERVED_SLUGS:
            errors["slug"] = (
                "Slug is reserved and cannot be used. Please choose another."
            )

        if errors:
            raise ValidationError(errors)

        return cleaned_data


class PostAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "title",
                    "content",
                    "content_html",
                    "tags",
                    "category",
                    "status",
                ]
            },
        ),
        (
            "Meta data",
            {
                "fields": [
                    "cover_image",
                    "header_image",
                    "slug",
                    "meta_description",
                    "view_count",
                    "order",
                    "keywords",
                    "content_update_at",
                ]
            },
        ),
    ]
    form = PostAdminForm
    readonly_fields = ["updated_at", "content_update_at"]
    list_display = [
        "title",
        "status",
        "created_at",
        "updated_at",
    ]  # 在列表中显示日期
    list_filter = ["status", "category"]  # 添加过滤器
    search_fields = ["title", "content"]  # 添加搜索功能


class CommentAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "content",
                    "post",
                    "guest",
                    "user_agent",
                    "OS",
                    "platform",
                    "browser",
                    "browser_version",
                ]
            },
        ),
        (
            "Time Information",
            {
                "fields": [
                    "created_at",
                    "updated_at",
                ]
            },
        ),
    ]

    readonly_fields = ["created_at", "updated_at"]
    list_display = ["content", "post", "guest", "created_at", "updated_at"]


class GalAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "vndb_id",
                    "title",
                    "title_cn",
                    # score
                    "character_score",
                    "story_score",
                    "comprehensive_score",
                    "vndb_rating",
                    # review
                    "summary",
                    "review",
                    "review_html",
                    "cover_image",
                ]
            },
        ),
        (
            "Time Information",
            {
                "fields": [
                    "created_at",
                    "updated_at",
                ]
            },
        ),
    ]

    readonly_fields = ["created_at", "updated_at"]
    list_display = ["vndb_id", "title", "created_at", "updated_at"]


class GuestAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "name",
                    "unique_id",
                    "email",
                    "password",
                    "provider",
                    "provider_id",
                    "avatar",
                    "is_admin",
                ]
            },
        ),
        (
            "Time Information",
            {
                "fields": [
                    "created_at",
                    "updated_at",
                    "last_visit",
                ]
            },
        ),
    ]

    readonly_fields = ["created_at", "updated_at", "last_visit"]
    list_display = ["name", "provider", "created_at", "updated_at"]
    list_filter = ["provider"]


class AnimeAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "mal_id",
                    "name",
                    "name_cn",
                    "year",
                    "synopsis",
                    "cover_image",
                    "rating",
                    "score",
                    "review",
                ]
            },
        ),
        (
            "Time Information",
            {
                "fields": [
                    "created_at",
                    "updated_at",
                ]
            },
        ),
    ]

    readonly_fields = ["created_at", "updated_at"]
    list_display = ["name", "created_at", "updated_at"]


admin.site.register(Post, PostAdmin)
admin.site.register(Guest, GuestAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Gal, GalAdmin)
admin.site.register(Anime, AnimeAdmin)
admin.site.register(Image, ImageAdmin)
