import json
from django.test import TestCase

from api.auth import TimeBaseAuth
from api.models import Guest, Post, Comment


class TestComment(TestCase):
    def setUp(self) -> None:
        Post.objects.create(
            title="comment test", content="comment test", slug="comment_test"
        )
        Guest.objects.create(
            unique_id="myself-114514", name="test-user", provider_id="114514"
        )

    def test_new_comment_endpoint(self) -> None:
        data = {
            "unique_id": "myself-114514",
            "content": "test comment",
            "post_id": Post.objects.get(title="comment test").pk,
            "metadata": {
                "user_agent": "UA",
                "platform": "Linux",
                "browser": "firefox",
                "browser_version": "114",
                "OS": "ArchLinux",
            },
        }

        # unauthed test
        response = self.client.post(
            "/api/comment/new",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

        # authed test
        token = TimeBaseAuth.create_token("test")
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.post(
            "/api/comment/new",
            data=json.dumps(data),
            headers=headers,
            content_type="application/json",
            # HTTP_AUTHORIZATION=f"Bearer {token}"  # or use this replace 'headers=headers'
        )
        self.assertEqual(response.status_code, 200)
        created_comment = Comment.objects.latest("id")
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], created_comment.pk)
