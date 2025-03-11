from django.contrib import admin

from .models import Post, Guest, Comment


class PostAdmin(admin.ModelAdmin):
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

    readonly_fields = ["update_at"]  # 将 update_at 设为只读
    list_display = ["title", "author", "created_at", "update_at"]  # 在列表中显示日期
    list_filter = ["status", "category", "author"]  # 添加过滤器
    search_fields = ["title", "content"]  # 添加搜索功能


admin.site.register(Post, PostAdmin)
admin.site.register(Guest)
admin.site.register(Comment)
