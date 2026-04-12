import shutil
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image as PILImage

from media_service.models import Image


@override_settings(SECURE_SSL_REDIRECT=False)
class ImageAdminTest(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.addCleanup(self.override.disable)

        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username="admin",
            email="admin@gsgfs.moe",
            password="passwd114",
        )
        self.client.force_login(self.admin_user)

    @staticmethod
    def generate_test_image(name="admin-test.png", size=(100, 100), color="red"):
        file = BytesIO()
        image = PILImage.new("RGB", size, color)
        image.save(file, format="PNG")
        file.seek(0)
        return SimpleUploadedFile(name, file.read(), content_type="image/png")

    def test_admin_upload_binds_current_user_as_uploader(self):
        response = self.client.post(
            reverse("admin:media_service_image_add"),
            {
                "file": self.generate_test_image(),
                "original_name": "admin-test.png",
                "alt_text": "admin upload",
                "description": "uploaded from admin",
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 302)

        image = Image.objects.get(original_name="admin-test.png")
        self.assertEqual(image.uploader, self.admin_user)
