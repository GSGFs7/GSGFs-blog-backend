import os
import time
from io import BytesIO

import blake3
import requests
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from PIL import Image as PILImage

from api.auth import TimeBaseAuth
from api.models import Image


class ImageUploadTest(TestCase):
    def setUp(self):
        self.client = Client()

    @staticmethod
    def generate_test_image(name="test.png", size=(100, 100), color="red"):
        file = BytesIO()
        image = PILImage.new("RGB", size, color)
        image.save(file, format="PNG")
        file.seek(0)
        return SimpleUploadedFile(name, file.read(), content_type="image/png")

    def test_upload(self):
        file = self.generate_test_image()
        token = TimeBaseAuth.create_token(f"test_{time.time()}")
        response = self.client.post(
            "/api/image/upload",
            {"file": file},
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Image.objects.filter(original_name="test.png").exists())

        hasher = blake3.blake3()
        for chunk in file.chunks():
            hasher.update(chunk)
        checksum = hasher.hexdigest()
        self.assertTrue(Image.objects.filter(resource__checksum=checksum).exists())


class ImageDeduplicationTest(TestCase):
    def setUp(self):
        self.client = Client()

    @staticmethod
    def generate_test_image(name="test.png", size=(100, 100), color="red"):
        file = BytesIO()
        image = PILImage.new("RGB", size, color)
        image.save(file, format="PNG")
        file.seek(0)
        return SimpleUploadedFile(name, file.read(), content_type="image/png")

    def test_duplicate_file_not_stored_twice(self):
        """Test that uploading the same image twice doesn't create duplicate files."""
        file1 = self.generate_test_image(name="first.png")
        token = TimeBaseAuth.create_token(f"test_{time.time()}")

        # First upload
        response1 = self.client.post(
            "/api/image/upload",
            {"file": file1},
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response1.status_code, 201)

        # Get the file path of first upload
        image1 = Image.objects.get(id=response1.json()["id"])
        file_path_1 = image1.resource.file.path

        # Second upload with same content but different name
        file2 = self.generate_test_image(name="second.png")
        token2 = TimeBaseAuth.create_token(f"test_{time.time()}_2")

        response2 = self.client.post(
            "/api/image/upload",
            {"file": file2},
            HTTP_AUTHORIZATION=f"Bearer {token2}",
        )
        self.assertEqual(response2.status_code, 201)

        # Get the file path of second upload
        image2 = Image.objects.get(id=response2.json()["id"])
        file_path_2 = image2.resource.file.path

        # Both should reference the same file
        self.assertEqual(file_path_1, file_path_2)

        # Check that the file exists
        self.assertTrue(os.path.exists(file_path_1))


class WebImageUploadTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.image_src = (
            "https://img.gsgfs.moe/img/1b987606005d9dc83312b987bad854a6.jpg"
        )

        try:
            resp = requests.get(self.image_src, timeout=5)
            resp.raise_for_status()
            self.image_content = resp.content
        except Exception as e:
            self.skipTest(f"Failed to fetch image: {e}")

    def test_image_upload(self):
        file = SimpleUploadedFile("test_image.jpg", self.image_content, "image/jpeg")
        token = TimeBaseAuth.create_token(f"test_{time.time()}")
        response = self.client.post(
            "/api/image/upload",
            {"file": file},
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Image.objects.filter(original_name="test_image.jpg").exists())

        # clean exif
        img = PILImage.open(BytesIO(self.image_content))
        buffer = BytesIO()
        img.save(buffer, format=img.format)

        # hash
        hasher = blake3.blake3()
        hasher.update(buffer.getvalue())
        checksum = hasher.hexdigest()
        self.assertTrue(Image.objects.filter(resource__checksum=checksum).exists())
