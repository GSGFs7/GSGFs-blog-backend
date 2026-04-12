import shutil
import tempfile
from io import BytesIO

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from PIL import Image as PILImage

from media_service.models import ImageResource
from media_service.tasks import process_image


@override_settings(SECURE_SSL_REDIRECT=False)
class MediaTasksTest(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.addCleanup(self.override.disable)

    @staticmethod
    def build_image_resource_content():
        buffer = BytesIO()
        image = PILImage.new("RGB", (100, 100), "blue")
        image.save(buffer, format="PNG")
        content = buffer.getvalue()
        return ContentFile(content, name="task-test.png"), len(content)

    def test_process_image_marks_resource_as_processed(self):
        file, size = self.build_image_resource_content()
        image_resource = ImageResource.objects.create(
            checksum="b" * 64,
            file=file,
            width=100,
            height=100,
            size=size,
            mime_type="image/png",
        )

        process_image(image_resource.id)
        image_resource.refresh_from_db()

        self.assertTrue(image_resource.is_processed)
