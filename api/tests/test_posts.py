from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from api.models import Post
from api.tasks import generate_post_embedding


@override_settings(
    SECURE_SSL_REDIRECT=False,
    # make celery sync run the function
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class TestPost(TestCase):
    def setUp(self):
        post = Post.objects.create(
            title="test", content="test content", slug="test", status="published"
        )
        # generate post embedding again
        # it may fail to auto sync generate
        generate_post_embedding(post.id)

    def test_post_embedding_generation(self):
        post = Post.objects.get(title="test")
        self.assertIsNotNone(post.embedding)


    def test_post_api(self):
        post = Post.objects.get(title="test")
        self.assertEqual(post.content, "test content")

        # test API is available
        response = self.client.get("/api/post/")
        self.assertContains(response, post.pk, status_code=200)

        response = self.client.get("/api/post/ids")
        self.assertContains(response, post.pk, status_code=200)

        response = self.client.get(f"/api/post/{post.pk}")
        self.assertContains(response, "test content", status_code=200)

        response = self.client.get(f"/api/post/{post.slug}")
        self.assertContains(response, "test content", status_code=200)

        response = self.client.get("/api/post/sitemap")
        self.assertContains(response, post.pk, status_code=200)

        response = self.client.get("/api/post/search?q=test")
        self.assertContains(response, "test content", status_code=200)

    def test_reserve_slug(self):
        # ORM methods, 'api/admin.py' not work
        error_post = None
        try:
            error_post = Post.objects.create(
                title="reserve slug test", content="reserve slug test", slug="posts"
            )
        except Exception as e:
            if isinstance(e, ValidationError):
                pass
            else:
                raise
        if error_post is not None:
            raise
