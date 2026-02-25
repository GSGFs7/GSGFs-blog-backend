from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.db import connection
from api.models import Post, Category, Tag

@override_settings(
    SECRET_KEY="test_secret_key",
    CELERY_TASK_ALWAYS_EAGER=True,
    SECURE_SSL_REDIRECT=False,
    # Disable logging to avoid clutter
    LOGGING_CONFIG=None
)
class TestPostPerformance(TestCase):
    def setUp(self):
        # Create categories and tags
        categories = [Category.objects.create(name=f"Category {i}") for i in range(5)]
        tags = [Tag.objects.create(name=f"Tag {i}") for i in range(10)]

        # Create posts
        for i in range(20):
            # Using update_or_create to avoid unique constraint issues if test runs multiple times (though DB is reset)
            post = Post.objects.create(
                title=f"Post {i}",
                content=f"Content {i}",
                slug=f"post-{i}",
                status="published",
                category=categories[i % 5]
            )
            post.tags.add(tags[i % 10], tags[(i + 1) % 10])

    def test_post_list_query_count(self):
        # Warm up to ensure any initial setup queries are done
        self.client.get("/api/post/?size=20")

        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/post/?size=20")
            self.assertEqual(response.status_code, 200)

        print(f"\nQuery count: {len(ctx.captured_queries)}")
        # Dump queries if needed for debugging
        # for q in ctx.captured_queries:
        #     print(q['sql'])

        # N+1 analysis:
        # 1 query for Count (pagination)
        # 1 query for Post list
        # For each post (20):
        #   1 query for Category (select_related needed)
        #   1 query for Tags (prefetch_related needed)
        # Total approx: 1 + 1 + 20 + 20 = 42 queries.

        self.assertLess(len(ctx.captured_queries), 5, "Query count is too high, N+1 optimization failed")
