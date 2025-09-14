from django.test import TestCase, override_settings

from api.models import Post


@override_settings(SECURE_SSL_REDIRECT=False)
class TestPost(TestCase):
    def setUp(self):
        Post.objects.create(title="test", content="test content", slug="test")

    def test_post(self):
        post = Post.objects.get(title="test")
        self.assertEqual(post.content, "test content")
