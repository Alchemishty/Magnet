from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.errors import StorageError
from app.repositories.s3_client import S3Client, get_s3_client


@pytest.fixture()
def mock_boto_client():
    return MagicMock()


@pytest.fixture()
def s3(mock_boto_client):
    with patch("app.repositories.s3_client.boto3") as mock_boto3:
        mock_boto3.client.return_value = mock_boto_client
        mock_boto_client.head_bucket.return_value = {}
        client = S3Client(
            endpoint_url="http://localhost:9000",
            access_key="test",
            secret_key="test",
            bucket="test-bucket",
        )
    client._client = mock_boto_client
    return client


class TestInit:
    def test_creates_boto3_client(self):
        with patch("app.repositories.s3_client.boto3") as mock_boto3:
            mock_client = MagicMock()
            mock_boto3.client.return_value = mock_client
            mock_client.head_bucket.return_value = {}

            S3Client(
                endpoint_url="http://localhost:9000",
                access_key="key",
                secret_key="secret",
                bucket="my-bucket",
            )

            mock_boto3.client.assert_called_once_with(
                "s3",
                endpoint_url="http://localhost:9000",
                aws_access_key_id="key",
                aws_secret_access_key="secret",
            )

    def test_creates_bucket_if_not_exists(self):
        with patch("app.repositories.s3_client.boto3") as mock_boto3:
            mock_client = MagicMock()
            mock_boto3.client.return_value = mock_client
            error = ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadBucket"
            )
            mock_client.head_bucket.side_effect = error

            S3Client(
                endpoint_url="http://localhost:9000",
                access_key="key",
                secret_key="secret",
                bucket="new-bucket",
            )

            mock_client.create_bucket.assert_called_once_with(Bucket="new-bucket")

    def test_skips_create_when_bucket_exists(self):
        with patch("app.repositories.s3_client.boto3") as mock_boto3:
            mock_client = MagicMock()
            mock_boto3.client.return_value = mock_client
            mock_client.head_bucket.return_value = {}

            S3Client(
                endpoint_url="http://localhost:9000",
                access_key="key",
                secret_key="secret",
                bucket="existing-bucket",
            )

            mock_client.create_bucket.assert_not_called()


class TestUploadFile:
    def test_uploads_and_returns_key(self, s3, mock_boto_client):
        result = s3.upload_file("/tmp/video.mp4", "uploads/video.mp4")

        mock_boto_client.upload_file.assert_called_once_with(
            "/tmp/video.mp4", "test-bucket", "uploads/video.mp4"
        )
        assert result == "uploads/video.mp4"

    def test_wraps_boto_error(self, s3, mock_boto_client):
        mock_boto_client.upload_file.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "fail"}}, "PutObject"
        )

        with pytest.raises(StorageError):
            s3.upload_file("/tmp/video.mp4", "uploads/video.mp4")


class TestDownloadFile:
    def test_downloads_and_returns_path(self, s3, mock_boto_client):
        result = s3.download_file("uploads/video.mp4", "/tmp/video.mp4")

        mock_boto_client.download_file.assert_called_once_with(
            "test-bucket", "uploads/video.mp4", "/tmp/video.mp4"
        )
        assert result == "/tmp/video.mp4"

    def test_wraps_boto_error(self, s3, mock_boto_client):
        mock_boto_client.download_file.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "not found"}}, "GetObject"
        )

        with pytest.raises(StorageError):
            s3.download_file("uploads/video.mp4", "/tmp/video.mp4")


class TestPresignedUploadUrl:
    def test_generates_presigned_put_url(self, s3, mock_boto_client):
        mock_boto_client.generate_presigned_url.return_value = "https://s3/presigned"

        result = s3.generate_presigned_upload_url(
            "uploads/file.mp4", "video/mp4", expires_in=600
        )

        mock_boto_client.generate_presigned_url.assert_called_once_with(
            "put_object",
            Params={
                "Bucket": "test-bucket",
                "Key": "uploads/file.mp4",
                "ContentType": "video/mp4",
            },
            ExpiresIn=600,
        )
        assert result == "https://s3/presigned"


class TestPresignedDownloadUrl:
    def test_generates_presigned_get_url(self, s3, mock_boto_client):
        mock_boto_client.generate_presigned_url.return_value = "https://s3/download"

        result = s3.generate_presigned_download_url("renders/out.mp4", expires_in=300)

        mock_boto_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "renders/out.mp4"},
            ExpiresIn=300,
        )
        assert result == "https://s3/download"


class TestDeleteObject:
    def test_deletes_object(self, s3, mock_boto_client):
        s3.delete_object("uploads/old.mp4")

        mock_boto_client.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key="uploads/old.mp4"
        )

    def test_wraps_boto_error(self, s3, mock_boto_client):
        mock_boto_client.delete_object.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "fail"}}, "DeleteObject"
        )

        with pytest.raises(StorageError):
            s3.delete_object("uploads/old.mp4")


class TestHeadObject:
    def test_returns_metadata(self, s3, mock_boto_client):
        mock_boto_client.head_object.return_value = {
            "ContentLength": 1024,
            "ContentType": "video/mp4",
        }

        result = s3.head_object("uploads/file.mp4")

        assert result == {"ContentLength": 1024, "ContentType": "video/mp4"}

    def test_returns_none_when_not_found(self, s3, mock_boto_client):
        mock_boto_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "not found"}}, "HeadObject"
        )

        result = s3.head_object("uploads/missing.mp4")

        assert result is None


class TestGetS3ClientFactory:
    @patch.dict(
        "os.environ",
        {
            "S3_ENDPOINT": "http://localhost:9000",
            "S3_ACCESS_KEY": "key",
            "S3_SECRET_KEY": "secret",
            "S3_BUCKET": "bucket",
        },
    )
    @patch("app.repositories.s3_client.S3Client")
    def test_creates_client_from_env(self, mock_cls):
        get_s3_client()

        mock_cls.assert_called_once_with(
            endpoint_url="http://localhost:9000",
            access_key="key",
            secret_key="secret",
            bucket="bucket",
        )

    @patch.dict("os.environ", {}, clear=True)
    def test_raises_when_bucket_missing(self):
        with pytest.raises(ValueError, match="S3_BUCKET"):
            get_s3_client()
