import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import os
import uuid

from adapters.repository.s3_repository import S3Repository

class TestS3RepositoryAsync(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.bucket_name = "test-bucket"
        self.video_mock = MagicMock()
        self.video_mock.user_email = "user@example.com"
        self.video_mock.file_name = "test.mp4"
        self.video_mock.content = b"dummy_content"

    @patch.dict(os.environ, {
        "ENV": "dev",
        "ENDPOINT_URL": "http://localhost:4566",
        "AWS_ACCESS_KEY_ID": "test-key",
        "AWS_SECRET_ACCESS_KEY": "test-secret",
        "REGION_NAME": "us-east-1"
    })
    def test_init_should_load_correct_env_vars(self):
        repo = S3Repository(self.bucket_name)
        self.assertEqual(repo.bucket_name, self.bucket_name)
        self.assertEqual(repo.env, "dev")
        self.assertEqual(repo.endpoint_url, "http://localhost:4566")
        self.assertEqual(repo.aws_access_key_id, "test-key")
        self.assertEqual(repo.aws_secret_access_key, "test-secret")
        self.assertEqual(repo.region_name, "us-east-1")

    @patch("aioboto3.Session.client")
    @patch("uuid.uuid4", return_value=uuid.UUID("12345678123456781234567812345678"))
    @patch.dict(os.environ, {
        "ENV": "dev",
        "ENDPOINT_URL": "http://localhost:4566",
        "AWS_ACCESS_KEY_ID": "test-key",
        "AWS_SECRET_ACCESS_KEY": "test-secret",
        "REGION_NAME": "us-east-1"
    })
    async def test_upload_video_success(self, mock_uuid, mock_client):
        # Arrange
        s3_client_mock = AsyncMock()
        mock_client.return_value.__aenter__.return_value = s3_client_mock

        s3_client_mock.list_objects_v2.return_value = {}

        repo = S3Repository(self.bucket_name)

        # Act
        file_key, error = await repo.upload_video(self.video_mock)

        # Assert
        expected_key = f"{self.video_mock.user_email}/{self.video_mock.file_name}/12345678-1234-5678-1234-567812345678_{self.video_mock.file_name}"
        self.assertEqual(file_key, expected_key)
        self.assertIsNone(error)
        s3_client_mock.list_objects_v2.assert_called_once()
        s3_client_mock.put_object.assert_any_await(Bucket=self.bucket_name, Key=f"{self.video_mock.user_email}/{self.video_mock.file_name}/")
        s3_client_mock.put_object.assert_any_await(Bucket=self.bucket_name, Key=expected_key, Body=self.video_mock.content)

    @patch("aioboto3.Session.client")
    @patch.dict(os.environ, {
        "ENV": "dev",
        "ENDPOINT_URL": "http://localhost:4566",
        "AWS_ACCESS_KEY_ID": "test-key",
        "AWS_SECRET_ACCESS_KEY": "test-secret",
        "REGION_NAME": "us-east-1"
    })
    async def test_upload_video_already_exists_should_raise(self, mock_client):
        s3_client_mock = AsyncMock()
        mock_client.return_value.__aenter__.return_value = s3_client_mock

        s3_client_mock.list_objects_v2.return_value = {"Contents": [{"Key": "some/key"}]}

        repo = S3Repository(self.bucket_name)

        with self.assertRaises(ValueError) as context:
            await repo.upload_video(self.video_mock)

        self.assertIn("já está carregado", str(context.exception))
        s3_client_mock.list_objects_v2.assert_called_once()

    @patch("aioboto3.Session.client", side_effect=Exception("Falha no S3"))
    @patch.dict(os.environ, {
        "ENV": "dev",
        "ENDPOINT_URL": "http://localhost:4566",
        "AWS_ACCESS_KEY_ID": "test-key",
        "AWS_SECRET_ACCESS_KEY": "test-secret",
        "REGION_NAME": "us-east-1"
    })
    async def test_upload_video_general_exception(self, mock_client):
        repo = S3Repository(self.bucket_name)

        with self.assertRaises(Exception) as context:
            await repo.upload_video(self.video_mock)

        self.assertIn("Falha no S3", str(context.exception))
