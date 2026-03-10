"""S3/MinIO storage client for asset and render storage."""

import logging
import os

import boto3
from botocore.exceptions import ClientError

from app.errors import StorageError

logger = logging.getLogger(__name__)


class S3Client:
    """Wraps boto3 S3 operations for asset and render storage."""

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
    ):
        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in {"404", "NoSuchBucket"}:
                logger.info("Bucket %s not found, creating", self._bucket)
                self._client.create_bucket(Bucket=self._bucket)
            else:
                raise StorageError(
                    f"Failed to check bucket {self._bucket}: {e}"
                ) from e

    def upload_file(self, local_path: str, s3_key: str) -> str:
        try:
            self._client.upload_file(local_path, self._bucket, s3_key)
        except ClientError as e:
            raise StorageError(f"Failed to upload {s3_key}: {e}") from e
        return s3_key

    def download_file(self, s3_key: str, local_path: str) -> str:
        try:
            self._client.download_file(self._bucket, s3_key, local_path)
        except ClientError as e:
            raise StorageError(f"Failed to download {s3_key}: {e}") from e
        return local_path

    def generate_presigned_upload_url(
        self, s3_key: str, content_type: str, expires_in: int = 3600
    ) -> str:
        return self._client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self._bucket,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )

    def generate_presigned_download_url(
        self, s3_key: str, expires_in: int = 3600
    ) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": s3_key},
            ExpiresIn=expires_in,
        )

    def delete_object(self, s3_key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=s3_key)
        except ClientError as e:
            raise StorageError(f"Failed to delete {s3_key}: {e}") from e

    def head_object(self, s3_key: str) -> dict | None:
        try:
            return self._client.head_object(Bucket=self._bucket, Key=s3_key)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in {"404", "NoSuchKey", "NotFound"}:
                return None
            raise StorageError(
                f"Failed to head {s3_key}: {e}"
            ) from e


def get_s3_client() -> S3Client:
    bucket = os.environ.get("S3_BUCKET")
    if not bucket:
        raise ValueError("S3_BUCKET environment variable is required")
    return S3Client(
        endpoint_url=os.environ.get("S3_ENDPOINT", "http://localhost:9000"),
        access_key=os.environ.get("S3_ACCESS_KEY", ""),
        secret_key=os.environ.get("S3_SECRET_KEY", ""),
        bucket=bucket,
    )
