import boto3
from datetime import datetime, timezone
import uuid


class DBRepository:
    """ Classe responsável pela interação com o banco de dados DynamoDB """
    def __init__(self, table_name):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def register_video(self, video, s3_key):
        """ Registra o vídeo no banco com status PENDENTE_PROCESSAMENTO """
        self.table.put_item(Item={
            "id": str(uuid.uuid4()),
            "user_email": video.user_email,
            "file_name": video.file_name,
            "s3_key": s3_key,
            "status": "PENDENTE_PROCESSAMENTO",
            "created_at": datetime.now(timezone.utc).isoformat()  # Corrected import
        })
