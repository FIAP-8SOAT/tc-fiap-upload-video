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


def test_upload_file_success(mock_upload_video_use_case):
    files = {
        "file": ("test_video.mp4", b"video content", "video/mp4")
    }
    headers = {
        "authorization": "Bearer valid_token"
    }
    response = client.post("/upload", files=files, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"details": {"status": "success"}}


def test_upload_file_invalid_token():
    files = {
        "file": ("test_video.mp4", b"video content", "video/mp4")
    }
    headers = {
        "authorization": "InvalidToken"
    }
    response = client.post("/upload", files=files, headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "Token inválido"}


def test_upload_file_exception(mock_upload_video_use_case):
    mock_upload_video_use_case.execute.side_effect = Exception("Unexpected error")
    files = {
        "file": ("test_video.mp4", b"video content", "video/mp4")
    }
    headers = {
        "authorization": "Bearer valid_token"
    }
    response = client.post("/upload", files=files, headers=headers)
    assert response.status_code == 500
    assert "Unexpected error" in response.json()["detail"]