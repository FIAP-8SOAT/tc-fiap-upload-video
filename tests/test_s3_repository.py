import unittest
from unittest.mock import patch, MagicMock
import os
import boto3
from moto import mock_aws  # ou mock_s3 se for a versão antiga
from adapters.repository.s3_repository import S3Repository

# Definimos fora da classe pois será usado pelos decorators
ENV_VARS = {
    "ENDPOINT_URL": "http://localhost:4566",
    "AWS_ACCESS_KEY_ID": "test-access-key",
    "AWS_SECRET_ACCESS_KEY": "test-secret-key",
    "REGION_NAME": "us-east-1"
}


class TestS3Repository(unittest.TestCase):
    def setUp(self):
        self.bucket_name = "test-bucket"

    @patch.dict(os.environ, {"ENV": "dev", **ENV_VARS})
    def test_init_with_dev_environment(self):
        repo = S3Repository(self.bucket_name)
        self.assertEqual(repo.bucket_name, self.bucket_name)
        self.assertIsNotNone(repo.s3)

    @patch.dict(os.environ, {"ENV": "prod", **ENV_VARS})
    def test_init_prod_environment(self):
        repo = S3Repository(self.bucket_name)
        self.assertEqual(repo.bucket_name, self.bucket_name)
        self.assertIsNotNone(repo.s3)

    @patch.dict(os.environ, {"ENV": "invalid"})
    def test_init_invalid_environment(self):
        with self.assertRaises(ValueError):
            S3Repository(self.bucket_name)

    @patch.dict(os.environ, {"ENV": "dev", **ENV_VARS})
    @mock_aws()
    def test_upload_video_success(self):
        conn = boto3.client('s3')
        conn.create_bucket(Bucket=self.bucket_name)

        repo = S3Repository(self.bucket_name)
        repo.s3 = conn

        video = MagicMock()
        video.user_email = "user@example.com"
        video.file_name = "test_video.mp4"
        video.content = b"test video content"

        file_key, error = repo.upload_video(video)

        self.assertIsNotNone(file_key)
        self.assertIsNone(error)
        self.assertIn(video.user_email, file_key)
        self.assertIn(video.file_name, file_key)

    @patch.dict(os.environ, {"ENV": "dev", **ENV_VARS})
    @mock_aws()
    def test_upload_video_duplicate(self):
        conn = boto3.client('s3')
        conn.create_bucket(Bucket=self.bucket_name)

        user_dir = "user@example.com/"
        video_dir = f"{user_dir}test_video.mp4/"
        conn.put_object(Bucket=self.bucket_name, Key=user_dir)
        conn.put_object(Bucket=self.bucket_name, Key=video_dir)

        repo = S3Repository(self.bucket_name)
        repo.s3 = conn

        video = MagicMock()
        video.user_email = "user@example.com"
        video.file_name = "test_video.mp4"
        video.content = b"test video content"

        with self.assertRaises(ValueError):
            repo.upload_video(video)

    @patch.dict(os.environ, {"ENV": "dev", **ENV_VARS})
    @mock_aws()
    def test_upload_video_bucket_creation(self):
        conn = boto3.client('s3')

        repo = S3Repository(self.bucket_name)
        repo.s3 = conn

        video = MagicMock()
        video.user_email = "user@example.com"
        video.file_name = "test_video.mp4"
        video.content = b"test video content"

        buckets = conn.list_buckets()['Buckets']
        bucket_names = [b['Name'] for b in buckets]
        self.assertIn(self.bucket_name, bucket_names)

    @patch.dict(os.environ, {"ENV": "dev", **ENV_VARS})
    @mock_aws()
    def test_upload_video_user_directory_creation(self):
        conn = boto3.client('s3')
        conn.create_bucket(Bucket=self.bucket_name)

        repo = S3Repository(self.bucket_name)
        repo.s3 = conn

        video = MagicMock()
        video.user_email = "newuser@example.com"
        video.file_name = "test_video.mp4"
        video.content = b"test video content"

        objects = conn.list_objects_v2(Bucket=self.bucket_name, Prefix=video.user_email)
        self.assertIn('Contents', objects)
