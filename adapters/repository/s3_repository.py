from boto3 import s3
from dotenv import load_dotenv
import os

import boto3
import uuid


def configure_s3_client(bucket_name_var):
    """Configures the S3 client based on the environment."""
    # Valid bucket name
    bucket_name = bucket_name_var

    # Create the bucket if it doesn't exist
    try:
        s3.head_bucket(Bucket=bucket_name)
    except s3.exceptions.ClientError:
        s3.create_bucket(Bucket=bucket_name)

    return s3


class S3Repository:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name

        # Load the appropriate .env file based on the ENV variable
        env = os.getenv("ENV", "dev")
        env_file = f"config/.env.{env}"
        load_dotenv(env_file)

        # Configure the S3 client
        if env == "dev":
            self.s3 = boto3.client(
                "s3",
                endpoint_url=os.getenv("ENDPOINT_URL"),
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("REGION_NAME"),
            )
        elif env == "prod":
            self.s3 = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("REGION_NAME"),
            )
        else:
            raise ValueError(f"Unknown environment: {env}")

    def upload_video(self, video):
        """Faz upload do vídeo para o S3"""
        # Ensure the bucket exists
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
        except self.s3.exceptions.ClientError:
            self.s3.create_bucket(Bucket=self.bucket_name)
            print(f"Bucket '{self.bucket_name}' created successfully.")

        # Diretório do usuário
        user_directory = f"{video.user_email}/"

        # Verifica se o diretório do usuário já existe
        existing_objects = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=user_directory)
        if 'Contents' not in existing_objects:
            # Diretório do usuário não existe, cria um objeto vazio para representá-lo
            self.s3.put_object(Bucket=self.bucket_name, Key=user_directory)

        # Caminho completo do arquivo (subpasta com o nome do vídeo)
        video_directory = f"{user_directory}{video.file_name}/"
        existing_video_objects = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=video_directory)
        if 'Contents' in existing_video_objects:
            # Retorna uma mensagem de erro indicando que o vídeo já existe
            raise ValueError(f"O vídeo '{video.file_name}' já está carregado. Por favor, consultar o status do vídeo.")

        # Cria a subpasta do vídeo
        self.s3.put_object(Bucket=self.bucket_name, Key=video_directory)

        # Faz o upload do vídeo
        file_key = f"{video_directory}{uuid.uuid4()}_{video.file_name}"
        self.s3.put_object(Bucket=self.bucket_name, Key=file_key, Body=video.content)

        return file_key, None
