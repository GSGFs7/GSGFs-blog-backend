from django.contrib import admin

from .models import Post, Guest, Comment, Gal


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
    list_display = [
        "title",
        "author",
        "status",
        "created_at",
        "update_at",
    ]  # 在列表中显示日期
    list_filter = ["status", "category", "author"]  # 添加过滤器
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
                    "update_at",
                ]
            },
        ),
    ]

    readonly_fields = ["created_at", "update_at"]
    list_display = ["content", "post", "guest", "created_at", "update_at"]


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
                    "update_at",
                ]
            },
        ),
    ]

    readonly_fields = ["created_at", "update_at"]
    list_display = ["vndb_id", "title", "created_at", "update_at"]


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
                    "update_at",
                    "last_visit",
                ]
            },
        ),
    ]

    readonly_fields = ["created_at", "update_at", "last_visit"]
    list_display = ["name", "provider", "created_at", "update_at"]
    list_filter = ["provider"]


admin.site.register(Post, PostAdmin)
admin.site.register(Guest, GuestAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Gal, GalAdmin)
