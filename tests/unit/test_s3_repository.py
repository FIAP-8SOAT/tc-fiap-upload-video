import json
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import os
import uuid

import boto3

from adapters.repository.s3_repository import S3Repository

class TestS3RepositoryAsync(unittest.IsolatedAsyncioTestCase):

    def test_mock_secretsmanager(self):
        mock_secret = {
            "AWS_ACCESS_KEY_ID": "texto",
            "AWS_SECRET_ACCESS_KEY": "texto"
        }

        with patch("boto3.client") as mock_client:
            # Mock the client and its get_secret_value method
            mock_instance = MagicMock()
            mock_instance.get_secret_value.return_value = {
                "SecretString": json.dumps(mock_secret)
            }
            mock_client.return_value = mock_instance

            # Code under test
            client = boto3.client('secretsmanager')
            response = client.get_secret_value(SecretId='my/aws/creds')
            secret = json.loads(response['SecretString'])

            os.environ["AWS_ACCESS_KEY_ID"] = secret["AWS_ACCESS_KEY_ID"]
            os.environ["AWS_SECRET_ACCESS_KEY"] = secret["AWS_SECRET_ACCESS_KEY"]

            # Assertions
            assert os.environ["AWS_ACCESS_KEY_ID"] == "texto"
            assert os.environ["AWS_SECRET_ACCESS_KEY"] == "texto"

    def setUp(self):
        self.bucket_name = "test-bucket"
        self.video_mock = MagicMock()
        self.video_mock.user_email = "user@example.com"
        self.video_mock.user_id = "123456"
        self.video_mock.file_name = "test.mp4"
        self.video_mock.content = b"dummy_content"
        # Mock SecretsManager
        self.secrets_patcher = patch("boto3.client")
        mock_client = self.secrets_patcher.start()
        mock_instance = MagicMock()
        mock_instance.get_secret_value.return_value = {
            "SecretString": json.dumps({
                "AWS_ACCESS_KEY_ID": "test-key",
                "AWS_SECRET_ACCESS_KEY": "test-secret"
            })
        }
        mock_client.return_value = mock_instance

    def tearDown(self):
        self.secrets_patcher.stop()

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
        expected_key = f"{self.video_mock.user_id}/{self.video_mock.file_name}/{self.video_mock.file_name}"
        self.assertEqual(file_key, expected_key)
        self.assertIsNone(error)
        s3_client_mock.list_objects_v2.assert_called_once()
        s3_client_mock.put_object.assert_any_await(Bucket=self.bucket_name, Key=f"{self.video_mock.user_id}/{self.video_mock.file_name}/")
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
