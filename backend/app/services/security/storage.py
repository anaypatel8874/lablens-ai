"""LabLens AI - Secure File Storage Service"""
import os
import io
from typing import Optional, Tuple
from app.core.config import get_settings
from app.core.security import encrypt_file_data, decrypt_file_data, generate_secure_filename
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class StorageService:
    def __init__(self):
        self.provider = settings.storage_endpoint
        self.bucket = settings.storage_bucket
        self.s3_client = None
        if self.provider:
            self._init_s3()

    def _init_s3(self):
        try:
            import boto3
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=self.provider,
                aws_access_key_id=settings.storage_access_key,
                aws_secret_access_key=settings.storage_secret_key,
                region_name=settings.storage_region,
            )
        except Exception as e:
            logger.error("Failed to init S3 client", error=str(e))

    async def save_file(
        self, file_bytes: bytes, original_filename: str, encrypt: bool = True
    ) -> Tuple[str, str]:
        """Save file and return (storage_path, secure_filename)."""
        secure_name = generate_secure_filename(original_filename)

        if encrypt:
            file_bytes = encrypt_file_data(file_bytes)

        if self.s3_client:
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket,
                    Key=secure_name,
                    Body=file_bytes,
                    ContentType=self._get_content_type(original_filename),
                    ServerSideEncryption="AES256",
                )
                return f"s3://{self.bucket}/{secure_name}", secure_name
            except Exception as e:
                logger.error("S3 upload failed, falling back to local", error=str(e))

        # Local fallback
        local_dir = "/tmp/lablens-uploads"
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, secure_name)
        with open(local_path, "wb") as f:
            f.write(file_bytes)

        return f"file://{local_path}", secure_name

    async def get_file(self, storage_path: str) -> bytes:
        """Retrieve file bytes."""
        if storage_path.startswith("s3://"):
            if self.s3_client:
                key = storage_path.replace(f"s3://{self.bucket}/", "")
                try:
                    response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
                    return response["Body"].read()
                except Exception as e:
                    logger.error("S3 download failed", error=str(e))

        elif storage_path.startswith("file://"):
            local_path = storage_path.replace("file://", "")
            if os.path.exists(local_path):
                with open(local_path, "rb") as f:
                    return f.read()

        raise FileNotFoundError(f"File not found: {storage_path}")

    async def delete_file(self, storage_path: str):
        """Delete file from storage."""
        if storage_path.startswith("s3://"):
            if self.s3_client:
                key = storage_path.replace(f"s3://{self.bucket}/", "")
                try:
                    self.s3_client.delete_object(Bucket=self.bucket, Key=key)
                    return
                except Exception as e:
                    logger.error("S3 delete failed", error=str(e))

        elif storage_path.startswith("file://"):
            local_path = storage_path.replace("file://", "")
            if os.path.exists(local_path):
                os.remove(local_path)

    def _get_content_type(self, filename: str) -> str:
        ext = filename.rsplit(".", 1)[-1].lower()
        types = {
            "pdf": "application/pdf",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
        }
        return types.get(ext, "application/octet-stream")
