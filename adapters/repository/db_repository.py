import os
import boto3
import uuid
import logging
from datetime import datetime, timezone
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class DBRepository:
    """Classe responsável pela interação com o banco de dados DynamoDB"""
    def __init__(self, table_name: str):
        env = os.getenv("ENV", "prod").lower()
        self.table_name = table_name
        self.env = env

        if env == "dev":
            logger.info("Inicializando DBRepository em modo DEV (LocalStack)")
            self.dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url="http://localhost:4566",  # LocalStack padrão
                region_name="us-east-1",
                aws_access_key_id="test",
                aws_secret_access_key="test"
            )
            self._ensure_table_exists()
        else:
            logger.info("Inicializando DBRepository em modo PROD (AWS)")
            self.dynamodb = boto3.resource('dynamodb')

        self.table = self.dynamodb.Table(self.table_name)

    def _ensure_table_exists(self):
        """Cria a tabela no LocalStack se ainda não existir"""
        try:
            existing_tables = self.dynamodb.meta.client.list_tables()["TableNames"]
            if self.table_name not in existing_tables:
                logger.warning(f"Tabela {self.table_name} não existe. Criando...")
                self.dynamodb.create_table(
                    TableName=self.table_name,
                    KeySchema=[
                        {"AttributeName": "id", "KeyType": "HASH"}
                    ],
                    AttributeDefinitions=[
                        {"AttributeName": "id", "AttributeType": "S"}
                    ],
                    BillingMode='PAY_PER_REQUEST'
                ).wait_until_exists()
                logger.info(f"Tabela {self.table_name} criada com sucesso.")
            else:
                logger.info(f"Tabela {self.table_name} já existe.")
        except ClientError as e:
            logger.error(f"Erro ao verificar/criar tabela: {e}")
            raise

    def register_video(self, video, s3_key: str):
        """Registra o vídeo no banco com status PENDENTE_PROCESSAMENTO"""
        try:
            item = {
                "id": str(uuid.uuid4()),
                "user_email": video.user_email,
                "file_name": video.file_name,
                "s3_key": s3_key,
                "status": "PENDENTE_PROCESSAMENTO",
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            logger.info(f"Inserindo item no DynamoDB: {item}")
            self.table.put_item(Item=item)

        except Exception as e:
            logger.error(f"Erro ao registrar vídeo no DynamoDB: {str(e)}")
            raise
