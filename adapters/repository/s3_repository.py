import json
import logging
import os
import uuid

import aioboto3
import boto3
from dotenv import load_dotenv

from infrastructure.logging.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class S3Repository:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        client = boto3.client('secretsmanager')
        response = client.get_secret_value(SecretId='my/aws/creds')
        secret = json.loads(response['SecretString'])

        os.environ["AWS_ACCESS_KEY_ID"] = secret["AWS_ACCESS_KEY_ID"]
        os.environ["AWS_SECRET_ACCESS_KEY"] = secret["AWS_SECRET_ACCESS_KEY"]

        # Load the appropriate .env file based on the ENV variable
        env = os.getenv("ENV", "dev")
        env_file = f"config/.env.{env}"
        load_dotenv(env_file)

        self.env = env
        self.endpoint_url = os.getenv("ENDPOINT_URL") if env == "dev" else None
        self.aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
        self.aws_secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
        self.region_name = os.getenv("REGION_NAME")

    async def upload_video(self, video):
        """Faz upload assíncrono do vídeo para o S3"""
        try:
            logger.info(f"Uploading video '{video.file_name}' to S3 bucket '{self.bucket_name}'")

            session = aioboto3.Session()
            async with session.client(
                    "s3",
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.region_name
            ) as s3:

                # Diretório do usuário
                user_directory = f"{video.user_email}/"
                video_directory = f"{user_directory}{video.file_name}/"
                file_key = f"{video_directory}{uuid.uuid4()}_{video.file_name}"

                # Verifica se o vídeo já existe
                response = await s3.list_objects_v2(Bucket=self.bucket_name, Prefix=video_directory)
                if 'Contents' in response:
                    raise ValueError(f"O vídeo '{video.file_name}' já está carregado. Por favor, consultar o status do vídeo.")

                # Garante criação das "pastas" (S3 é flat, mas usamos chaves simulando diretórios)
                await s3.put_object(Bucket=self.bucket_name, Key=video_directory)

                # Upload do vídeo
                await s3.put_object(Bucket=self.bucket_name, Key=file_key, Body=video.content)

                return file_key, None

        except Exception as e:
            logger.error(f"Erro no upload do vídeo: {e}")
            raise
