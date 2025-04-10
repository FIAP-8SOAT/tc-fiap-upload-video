import json
import os
from application.use_cases.upload_video import UploadVideoUseCase
from adapters.repository.s3_repository import S3Repository
from adapters.repository.db_repository import DBRepository

# Configuração dos repositórios
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "meu-bucket-de-videos")
DYNAMO_TABLE_NAME = os.getenv("DYNAMO_TABLE_NAME", "uploads_videos")

s3_repo = S3Repository(S3_BUCKET_NAME)
db_repo = DBRepository(DYNAMO_TABLE_NAME)

use_case = UploadVideoUseCase(s3_repo, db_repo)


def lambda_handler(event, context):
    """ Entrada principal da Lambda """
    try:
        # Lendo o modo de execução (padrão é False)
        simulate = event.get("queryStringParameters", {}).get("simulate", "false").lower() == "true"

        token = event['headers'].get("Authorization")
        if not token:
            return response(401, {"error": "Token não encontrado"})

        files = event['files']

        result, status = use_case.execute(files, token, simulate)
        return response(status, result)

    except Exception as e:
        return response(500, {"error": str(e)})


def response(status, body):
    """ Formata resposta HTTP """
    return {
        "statusCode": status,
        "body": json.dumps(body),
        "headers": {"Content-Type": "application/json"}
    }
