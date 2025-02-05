from django.contrib import admin

from .models import Post, Guest


class PostAdmin(admin.ModelAdmin):
    readonly_fields = (
        "created_at",
        "update_at",
    )
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "title",
                    "content",
                    "content_html",
                    "author",
                    "tags",
                    "category",
                    "status",
                ]
            },
        ),
        ("Date information", {"fields": ["created_at", "update_at"]}),
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
                ]
            },
        ),
    ]


admin.site.register(Post, PostAdmin)
admin.site.register(Guest)
