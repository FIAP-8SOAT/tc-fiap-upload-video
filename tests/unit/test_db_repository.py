import os
import pytest
from unittest import mock
import boto3
from adapters.repository.db_repository import DBRepository


class FakeVideo:
    def __init__(self, user_email, file_name):
        self.user_email = user_email
        self.file_name = file_name


@pytest.fixture
def mock_dynamodb(mocker):
    mock_dynamodb_resource = mocker.patch("boto3.resource")
    mock_dynamodb_client = mock.Mock()
    mock_dynamodb_resource.return_value = mock_dynamodb_client

    mock_dynamodb_client.meta.client.list_tables.return_value = {"TableNames": ["Videos"]}

    mock_table = mock.Mock()
    mock_dynamodb_client.Table.return_value = mock_table

    mock_table.table_name = "TestTable"

    mock_table.scan.return_value = {
        "Items": [
            {"user_email": "user@example.com", "file_name": "video.mp4", "s3_key": "s3/test/video.mp4", "status": "PENDENTE_PROCESSAMENTO", "created_at": "2025-04-13T12:00:00"}
        ]
    }

    return mock_dynamodb_client


def test_init_dev_environment_creates_table_if_not_exists(mock_dynamodb):
    os.environ["ENV"] = "dev"
    repo = DBRepository("TestTable")
    assert repo.env == "dev"
    assert repo.table.table_name == "TestTable"


def test_table_is_created_if_not_exists(mock_dynamodb):
    os.environ["ENV"] = "dev"
    dynamodb = boto3.resource("dynamodb", region_name=os.getenv("REGION_NAME"))
    table_names = dynamodb.meta.client.list_tables()["TableNames"]
    assert "Videos" in table_names


def test_register_video_inserts_item(mock_dynamodb):
    os.environ["ENV"] = "dev"
    repo = DBRepository("Videos")
    video = FakeVideo("user@example.com", "video.mp4")
    repo.register_video(video)

    response = repo.table.scan()
    items = response['Items']
    assert len(items) == 1
    assert items[0]['user_email'] == "user@example.com"
    assert items[0]['file_name'] == "video.mp4"
    assert items[0]['s3_key'] == "s3/test/video.mp4"
    assert items[0]['status'] == "PENDENTE_PROCESSAMENTO"
    assert "created_at" in items[0]


def test_ensure_table_exists_raises_exception_on_error(mock_dynamodb, mocker):
    mock_dynamodb.meta.client.list_tables.side_effect = Exception("Falha")

    os.environ["ENV"] = "dev"
    with pytest.raises(Exception, match="Falha"):
        DBRepository("AnyTable")


def test_register_video_logs_error_on_failure(caplog, mock_dynamodb):
    os.environ["ENV"] = "dev"
    repo = DBRepository("Videos")

    with mock.patch.object(repo.table, "put_item", side_effect=Exception("Erro")):
        with pytest.raises(Exception, match="Erro"):
            repo.register_video(FakeVideo("a@a.com", "b.mp4"))

    assert "Erro ao registrar vídeo no DynamoDB" in caplog.text
