import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from main import app

client = TestClient(app)


@pytest.fixture
def mock_upload_video_use_case():
    with patch("main.UploadVideoUseCase") as mock:
        mock_instance = mock.return_value
        mock_instance.execute = AsyncMock(return_value={"status": "success"})
        yield mock_instance


# Positive Test Cases
def test_upload_file_valid(mock_upload_video_use_case):
    files = {
        "file": ("test_video.mp4", b"video content", "video/mp4")
    }
    headers = {
        "authorization": "Bearer valid_token"
    }
    response = client.post("/upload", files=files, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"details": {"status": "success"}}


def test_upload_multiple_files_valid(mock_upload_video_use_case):
    files = [
        ("file", ("test_video1.mp4", b"video content 1", "video/mp4")),
        ("file", ("test_video2.mp4", b"video content 2", "video/mp4"))
    ]
    headers = {
        "authorization": "Bearer valid_token"
    }
    response = client.post("/upload", files=files, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"details": {"status": "success"}}


# Negative Test Cases
def test_upload_missing_authorization_header():
    files = {
        "file": ("test_video.mp4", b"video content", "video/mp4")
    }
    headers = {
        "authorization": ""
    }
    response = client.post("/upload", files=files, headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "Token inválido"}


def test_upload_invalid_token_format():
    files = {
        "file": ("test_video.mp4", b"video content", "video/mp4")
    }
    headers = {
        "authorization": "InvalidToken"
    }
    response = client.post("/upload", files=files, headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "Token inválido"}


def test_upload_empty_file(mock_upload_video_use_case):
    files = {}
    headers = {
        "authorization": "Bearer valid_token"
    }
    response = client.post("/upload", files=files, headers=headers)

    assert response.status_code == 422
    assert response.json() == {"detail": [{"loc": ["body", "file"], "msg": "field required", "type": "value_error.missing"}]}


def test_upload_unsupported_file_type(mock_upload_video_use_case):
    files = {
        "file": ("test.txt", b"text content", "text/plain")
    }
    headers = {
        "authorization": "Bearer valid_token",
        "Content-Type": "text/plain"
    }
    response = client.post("/upload", files=files, headers=headers)

    assert response.status_code == 422


def test_upload_missing_file(mock_upload_video_use_case):
    headers = {
        "authorization": "Bearer valid_token"
    }
    response = client.post("/upload", headers=headers)
    assert response.status_code == 422


def test_upload_invalid_content_type():
    files = {
        "file": ("test_video.mp4", b"video content", "video/mp4")
    }
    headers = {
        "authorization": "Bearer valid_token",
        "Content-Type": "application/json"
    }
    response = client.post("/upload", files=files, headers=headers)
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "field required"


def test_upload_file_exceeds_max_size(mock_upload_video_use_case):
    # Simulate the use case returning an error for large files
    mock_upload_video_use_case.execute.return_value = {
        "status": "Erro: Tamanho máximo permitido é 50MB"
    }
    large_file_content = b"a" * ((50 * 1024 * 1024) + 10000)  # 50MB + 1 byte
    files = {
        "file": ("large_video.mp4", large_file_content, "video/mp4")
    }
    headers = {
        "authorization": "Bearer valid_token"
    }
    response = client.post("/upload", files=files, headers=headers)
    assert response.status_code == 200
    assert "Erro: Tamanho máximo permitido é 50MB" in response.json()["details"]["status"]


def test_upload_file_invalid_media_type(mock_upload_video_use_case):
    # Simulate the use case returning an error for invalid media types
    mock_upload_video_use_case.execute.return_value = {
        "status": "Erro: Tipo de mídia inválido"
    }
    files = {
        "file": ("test_video.avi", b"video content", "video/avi")
    }
    headers = {
        "authorization": "Bearer valid_token"
    }
    response = client.post("/upload", files=files, headers=headers)
    assert response.status_code == 200
    assert "Erro: Tipo de mídia inválido" in response.json()["details"]["status"]


def test_upload_internal_server_error(mock_upload_video_use_case):
    mock_upload_video_use_case.execute.side_effect = Exception("Unexpected error")
    files = {
        "file": ("test_video.mp4", b"video content", "video/mp4")
    }
    headers = {
        "authorization": "Bearer valid_token"
    }
    response = client.post("/upload", files=files, headers=headers)
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error."}


def test_upload_repository_initialization_error():
    with patch("main.S3Repository", side_effect=Exception("S3 initialization error")):
        files = {
            "file": ("test_video.mp4", b"video content", "video/mp4")
        }
        headers = {
            "authorization": "Bearer valid_token"
        }
        response = client.post("/upload", files=files, headers=headers)
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error."}
