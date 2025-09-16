from django.test import TestCase, override_settings

from api.models import Post


@override_settings(SECURE_SSL_REDIRECT=False)
class TestPost(TestCase):
    def setUp(self):
        Post.objects.create(title="test", content="test content", slug="test")

    def test_post(self):
        post = Post.objects.get(title="test")
        self.assertEqual(post.content, "test content")

        # test API is available
        response = self.client.get("/api/post/")
        self.assertContains(response, post.pk, status_code=200)

        response = self.client.get("/api/post/posts")
        self.assertContains(response, post.pk, status_code=200)

        response = self.client.get(f"/api/post/{post.pk}")
        self.assertContains(response, "test content", status_code=200)

        response = self.client.get("/api/post/sitemap")
        self.assertContains(response, post.pk, status_code=200)

        response = self.client.get("/api/post/search?q=test")
        self.assertContains(response, "test content", status_code=200)
