from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from api.utils import chinese_slugify, extract_front_matter

from .models import Anime, Comment, Gal, Guest, Post


class PostAdminForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = "__all__"

    def clean(self):
        """
        Cleans and validates form data for a Post model.

        - Extracts metadata from the 'content' field using front matter if available.
        - If 'title' is missing, attempts to extract it from metadata; checks for uniqueness.
        - Automatically generates 'slug' from metadata or the title if not provided.
        - Collects validation errors for missing or duplicate fields and raises ValidationError if any are found.

        Returns:
            dict: The cleaned and possibly modified form data.

        Raises:
            ValidationError: If required fields are missing, cannot be extracted/generated, or if the title is not unique.
        """

        cleaned_data = super().clean()
        title = cleaned_data.get("title")
        content = cleaned_data.get("content")

        metadata = {}
        errors = {}

        if content:
            metadata = extract_front_matter(content)
        else:
            errors["content"] = "Content field cannot be empty."

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
                    "The title field cannot be empty and cannot be automatically extracted from Front Matter."
                )

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
                ]
            },
        ),
    ]
    form = PostAdminForm
    readonly_fields = ["updated_at"]  # 将 updated_at 设为只读
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
