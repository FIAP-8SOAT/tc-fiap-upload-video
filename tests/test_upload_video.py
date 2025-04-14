import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, UploadFile
from application.use_cases.upload_video import UploadVideoUseCase
from domain.entities.video import Video


@pytest.fixture
def mock_s3_repo():
    return MagicMock()

@pytest.fixture
def mock_db_repo():
    return MagicMock()

@pytest.fixture
def upload_video_use_case(mock_s3_repo, mock_db_repo):
    return UploadVideoUseCase(mock_s3_repo, mock_db_repo)

@pytest.mark.asyncio
async def test_execute_successful_upload(upload_video_use_case, mock_s3_repo, mock_db_repo):
    mock_token = "valid_token"
    mock_user_email = "user@example.com"
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "video.mp4"
    mock_file.read.return_value = b"fake_video_content"

    with patch("application.services.token_service.TokenService.extract_user_email", return_value=mock_user_email):
        response = await upload_video_use_case.execute([mock_file], mock_token)

    assert len(response) == 1
    assert response[0]["status"] == "Sucesso"
    mock_s3_repo.upload_video.assert_called_once()
    mock_db_repo.register_video.assert_called_once()

@pytest.mark.asyncio
async def test_execute_token_missing_email(upload_video_use_case):
    mock_token = "invalid_token"
    mock_file = AsyncMock(spec=UploadFile)

    with patch("application.services.token_service.TokenService.extract_user_email", return_value=None):
        with pytest.raises(HTTPException) as exc_info:
            await upload_video_use_case.execute([mock_file], mock_token)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "E-mail não encontrado no Token"

@pytest.mark.asyncio
async def test_execute_exceeds_max_files(upload_video_use_case):
    mock_token = "valid_token"
    mock_user_email = "user@example.com"
    mock_files = [AsyncMock(spec=UploadFile) for _ in range(6)]

    with patch("application.services.token_service.TokenService.extract_user_email", return_value=mock_user_email):
        with pytest.raises(HTTPException) as exc_info:
            await upload_video_use_case.execute(mock_files, mock_token)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Máximo de 5 vídeos permitidos"

@pytest.mark.asyncio
async def test_execute_file_exceeds_max_size(upload_video_use_case):
    mock_token = "valid_token"
    mock_user_email = "user@example.com"
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "large_video.mp4"
    mock_file.read.return_value = b"a" * (50 * 1024 * 1024 + 1)  # Exceeds 50MB

    with patch("application.services.token_service.TokenService.extract_user_email", return_value=mock_user_email):
        response = await upload_video_use_case.execute([mock_file], mock_token)

    assert len(response) == 1
    assert response[0]["status"] == "Erro: Tamanho máximo permitido é 50MB"

@pytest.mark.asyncio
async def test_execute_s3_upload_error(upload_video_use_case, mock_s3_repo):
    mock_token = "valid_token"
    mock_user_email = "user@example.com"
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "video.mp4"
    mock_file.read.return_value = b"fake_video_content"
    mock_s3_repo.upload_video.side_effect = Exception("S3 upload error")

    with patch("application.services.token_service.TokenService.extract_user_email", return_value=mock_user_email):
        response = await upload_video_use_case.execute([mock_file], mock_token)

    assert len(response) == 1
    assert response[0]["status"] == "Erro: S3 upload error"

@pytest.mark.asyncio
async def test_execute_db_register_error(upload_video_use_case, mock_s3_repo, mock_db_repo):
    mock_token = "valid_token"
    mock_user_email = "user@example.com"
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "video.mp4"
    mock_file.read.return_value = b"fake_video_content"
    mock_db_repo.register_video.side_effect = Exception("DB register error")

    with patch("application.services.token_service.TokenService.extract_user_email", return_value=mock_user_email):
        response = await upload_video_use_case.execute([mock_file], mock_token)

    assert len(response) == 1
    assert response[0]["status"] == "Erro: DB register error"