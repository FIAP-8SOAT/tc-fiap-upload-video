import asyncio
import os

import boto3
import uuid
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DBRepository:
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
        else:
            logger.info("Inicializando DBRepository em modo PROD (AWS)")
            self.dynamodb = boto3.resource('dynamodb', region_name=os.getenv("REGION_NAME"))

            # Buscar e exibir o endpoint URL apenas em produção
            logger.info(f"Endpoint URL do DynamoDB (AWS): {self.dynamodb.meta.client.meta.endpoint_url}")

        self._ensure_table_exists()
        self.table = self.dynamodb.Table(self.table_name)

    def _ensure_table_exists(self):
        try:
            existing_tables = self.dynamodb.meta.client.list_tables()["TableNames"]
            if self.table_name not in existing_tables:
                logger.warning(f"Tabela {self.table_name} não existe. Criando...")
                self.dynamodb.create_table(
                    TableName=self.table_name,
                    KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
                    AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
                    BillingMode='PAY_PER_REQUEST'
                ).wait_until_exists()
                logger.info(f"Tabela {self.table_name} criada com sucesso.")
            else:
                logger.info(f"Tabela {self.table_name} já existe.")
        except ClientError as e:
            logger.error(f"Erro ao verificar/criar tabela: {e}")
            raise

    async def register_video(self, video):
        try:
            item = {
                "id": str(uuid.uuid4()),
                "ID_USUARIO": video.user_id,
                "EMAIL": video.user_email,
                "STATUS_PROCESSAMENTO": "PENDENTE_PROCESSAMENTO",
                "URL_DOWNLOAD": "",
                "NOME_VIDEO": video.file_name
            }

            logger.info(f"Inserindo item no DynamoDB: {item}")
            await asyncio.to_thread(self.table.put_item, Item=item)

        except Exception as e:
            logger.error(f"Erro ao registrar vídeo no DynamoDB: {str(e)}")
            raise
