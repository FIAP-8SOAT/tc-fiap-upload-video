import boto3
import uuid


class S3Repository:
    def __init__(self, bucket_name):
        self.s3 = boto3.client('s3')
        self.bucket_name = bucket_name

    def upload_video(self, video):
        """ Faz upload do vídeo para o S3 """
        file_key = f"{video.user_email}/{uuid.uuid4()}_{video.file_name}"
        self.s3.put_object(Bucket=self.bucket_name, Key=file_key, Body=video.content)
        return file_key
