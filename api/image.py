import hashlib
import io
import mimetypes
import os
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from dotenv import load_dotenv
from PIL import Image as PILImage


class ImageUploadService:
    """Upload image to OSS"""

    def __init__(self):
        self.endpoint_url = os.environ.get("R2_ENDPOINT_URL")
        self.r2_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=os.environ.get("R2_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("R2_SECRET_ACCESS_KEY"),
        )
        self.bucket_name = os.environ.get("R2_BUCKET_NAME", "img")
        self.public_url = os.environ.get("R2_PUBLIC_URL")

    def validate_image(self, file: InMemoryUploadedFile) -> Dict[str, Any]:
        """Validate image file"""
        try:
            img = PILImage.open(file)
            img.verify()
            file.seek(0)  # Reset file pointer after verification
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
            }
        except Exception as e:
            raise ValueError(f"Invalid image file: {e}")

    def generate_file_path(self, file: InMemoryUploadedFile) -> str:
        """Generate a unique file path for the image"""
        ext = file.name.split(".")[-1]

        hashed = hashlib.md5(file.read()).hexdigest()
        file.seek(0)

        unique_filename = f"{hashed}.{ext}"
        return f"img/{unique_filename}"

    def upload_to_r2(self, file: InMemoryUploadedFile, file_path: str) -> str:
        """Upload image to R2"""
        try:
            self.r2_client.upload_fileobj(
                file,
                self.bucket_name,
                file_path,
            )

            if self.public_url:
                return f"{self.public_url}/{file_path}"
            else:
                return f"https://{self.endpoint_url}/{file_path}"
        except ClientError as e:
            raise Exception(f"Failed to upload image: {e}")

    def test_list_buckets(self):
        for bucket in self.r2_client.list_buckets()["Buckets"]:
            print(f"{bucket['Name']}")

    def test_list_objects(self):
        try:
            response = self.r2_client.list_objects_v2(Bucket=self.bucket_name)
            if "Contents" in response:
                for obj in response["Contents"]:
                    print(obj)
            else:
                print("No objects found in the bucket.")
        except ClientError as e:
            print(f"Error listing objects: {e}")

    def test_upload_image(self, file: str):
        """Test upload image"""
        with open(file, "rb") as f:
            # 获取正确的 MIME 类型
            content_type, _ = mimetypes.guess_type(file)
            if not content_type or not content_type.startswith("image/"):
                content_type = "image/jpeg"  # 默认值

            uploaded_file = InMemoryUploadedFile(
                file=f,
                field_name=None,
                name=os.path.basename(file),
                content_type=content_type,
                size=os.path.getsize(file),
                charset=None,
            )
            self.validate_image(uploaded_file)
            file_path = self.generate_file_path(uploaded_file)
            url = self.upload_to_r2(uploaded_file, file_path)
            print(f"Image uploaded to: {url}")


if __name__ == "__main__":
    load_dotenv(".env")
    s = ImageUploadService()
    s.test_upload_image("/home/jh/Pictures/Noir_and_Neri.jpg")
