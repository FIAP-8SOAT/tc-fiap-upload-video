import os
import pytest
from unittest import mock
from adapters.repository.db_repository import DBRepository


class FakeVideo:
    def __init__(self, user_email, file_name, user_id="fake_id"):
        self.user_email = user_email
        self.file_name = file_name
        self.user_id = user_id


@pytest.fixture
def mock_dynamodb(mocker):
    # Mock do recurso DynamoDB do boto3
    mock_dynamodb_resource = mocker.patch("boto3.resource")
    mock_dynamodb_client = mock.Mock()
    mock_dynamodb_resource.return_value = mock_dynamodb_client

    # Mock das tabelas existentes
    mock_dynamodb_client.meta.client.list_tables.return_value = {"TableNames": ["Videos"]}

    # Mock de uma tabela e dados de vídeo simulados
    mock_table = mock.Mock()
    mock_dynamodb_client.Table.return_value = mock_table

    mock_table.table_name = "Videos"

    # Mock do retorno de dados da tabela
    mock_table.scan.return_value = {
        "Items": [
            {"id": "fake-uuid", "EMAIL": "user@example.com", "NOME_VIDEO": "video.mp4",
             "STATUS_PROCESSAMENTO": "PENDENTE_PROCESSAMENTO", "URL_DOWNLOAD": "", "created_at": "2025-04-13T12:00:00"}
        ]
    }

    return mock_dynamodb_client


@pytest.mark.asyncio
async def test_register_video_inserts_item(mock_dynamodb):
    os.environ["ENV"] = "dev"
    repo = DBRepository("Videos")

    video = FakeVideo("user@example.com", "video.mp4", user_id="user-123")
    await repo.register_video(video)

    # Verifica se o item foi inserido na tabela corretamente
    response = repo.table.scan()
    items = response['Items']
    assert len(items) == 1
    assert items[0]['EMAIL'] == "user@example.com"
    assert items[0]['NOME_VIDEO'] == "video.mp4"
    assert items[0]['STATUS_PROCESSAMENTO'] == "PENDENTE_PROCESSAMENTO"
    assert "created_at" in items[0]


@pytest.mark.asyncio
async def test_register_video_logs_error_on_failure(caplog, mock_dynamodb):
    os.environ["ENV"] = "dev"
    repo = DBRepository("Videos")

    # Simulando uma falha no put_item
    with mock.patch.object(repo.table, "put_item", side_effect=Exception("Erro")):
        with pytest.raises(Exception, match="Erro"):
            await repo.register_video(FakeVideo("a@a.com", "b.mp4"))

    # Verifica se o log de erro foi gerado
    assert "Erro ao registrar vídeo no DynamoDB" in caplog.text


@pytest.mark.asyncio
async def test_ensure_table_exists_raises_exception_on_error(mock_dynamodb, mocker):
    # Simulando erro na listagem de tabelas
    mock_dynamodb.meta.client.list_tables.side_effect = Exception("Falha")

    os.environ["ENV"] = "dev"
    with pytest.raises(Exception, match="Falha"):
        DBRepository("AnyTable")
