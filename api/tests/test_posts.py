from django.test import TestCase

from api.models import Post


class TestPost(TestCase):
    def setUp(self):
        Post.objects.create(title="test", content="test content", slug="test")

    def test_post(self):
        post = Post.objects.get(title="test")
        self.assertEqual(post.content, "test content")
    
