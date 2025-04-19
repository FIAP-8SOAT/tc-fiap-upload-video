import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, UploadFile
from application.use_cases.upload_video import UploadVideoUseCase
from adapters.repository.s3_repository import S3Repository
from adapters.repository.db_repository import DBRepository


@pytest.mark.asyncio
class TestUploadVideoUseCase:

    @pytest.fixture
    def setup_use_case(self):
        s3_repo = AsyncMock(spec=S3Repository)
        db_repo = AsyncMock(spec=DBRepository)
        use_case = UploadVideoUseCase(s3_repo=s3_repo, db_repo=db_repo)
        return use_case, s3_repo, db_repo

    @pytest.fixture
    def mock_token_service(self):
        with patch("application.services.token_service.TokenService.extract_user_email_and_user_id") as mock:
            yield mock

    @pytest.fixture
    def mock_upload_file(self):
        def create_mocked_file(filename, content_type, size):
            file = MagicMock(spec=UploadFile)
            file.filename = filename
            file.content_type = content_type
            file.read = AsyncMock(return_value=b"a" * size)
            return file
        return create_mocked_file

    async def test_execute_success(self, setup_use_case, mock_token_service, mock_upload_file):
        use_case, s3_repo, db_repo = setup_use_case
        mock_token_service.return_value = ("user@example.com", "12345")
        file = mock_upload_file("video.mp4", "video/mp4", 10 * 1024 * 1024)

        response = await use_case.execute([file], token="mock_token")

        assert response[0]["status"] == "Sucesso"
        s3_repo.upload_video.assert_called_once()
        db_repo.register_video.assert_called_once()

    async def test_execute_no_email_in_token(self, setup_use_case, mock_token_service, mock_upload_file):
        use_case, _, _ = setup_use_case
        mock_token_service.return_value = (None, "12345")
        file = mock_upload_file("video.mp4", "video/mp4", 10 * 1024 * 1024)

        with pytest.raises(HTTPException) as exc:
            await use_case.execute([file], token="mock_token")

        assert exc.value.status_code == 403
        assert exc.value.detail == "E-mail não encontrado no Token"

    async def test_execute_no_user_id_in_token(self, setup_use_case, mock_token_service, mock_upload_file):
        use_case, _, _ = setup_use_case
        mock_token_service.return_value = ("user@example.com", None)
        file = mock_upload_file("video.mp4", "video/mp4", 10 * 1024 * 1024)

        with pytest.raises(HTTPException) as exc:
            await use_case.execute([file], token="mock_token")

        assert exc.value.status_code == 403
        assert exc.value.detail == "Usuário não encontrado no Token"

    async def test_execute_more_than_5_files(self, setup_use_case, mock_token_service, mock_upload_file):
        use_case, _, _ = setup_use_case
        mock_token_service.return_value = ("user@example.com", "12345")
        files = [mock_upload_file(f"video_{i}.mp4", "video/mp4", 10 * 1024 * 1024) for i in range(6)]

        with pytest.raises(HTTPException) as exc:
            await use_case.execute(files, token="mock_token")

        assert exc.value.status_code == 400
        assert exc.value.detail == "Máximo de 5 vídeos permitidos"

    async def test_execute_no_files(self, setup_use_case, mock_token_service):
        use_case, _, _ = setup_use_case
        mock_token_service.return_value = ("user@example.com", "12345")

        with pytest.raises(HTTPException) as exc:
            await use_case.execute([], token="mock_token")

        assert exc.value.status_code == 400
        assert exc.value.detail == "Não há arquivos para upload."

    async def test_execute_file_exceeds_size(self, setup_use_case, mock_token_service, mock_upload_file):
        use_case, _, _ = setup_use_case
        mock_token_service.return_value = ("user@example.com", "12345")
        file = mock_upload_file("video.mp4", "video/mp4", 60 * 1024 * 1024)

        response = await use_case.execute([file], token="mock_token")

        assert response[0]["status"] == "Erro: Tamanho máximo permitido é 50MB"

    async def test_execute_invalid_file_type(self, setup_use_case, mock_token_service, mock_upload_file):
        use_case, _, _ = setup_use_case
        mock_token_service.return_value = ("user@example.com", "12345")
        file = mock_upload_file("video.avi", "video/avi", 10 * 1024 * 1024)

        response = await use_case.execute([file], token="mock_token")

        assert response[0]["status"] == "Erro: Tipo de mídia inválido: video/avi"

    async def test_execute_error_in_s3_upload(self, setup_use_case, mock_token_service, mock_upload_file):
        use_case, s3_repo, _ = setup_use_case
        mock_token_service.return_value = ("user@example.com", "12345")
        file = mock_upload_file("video.mp4", "video/mp4", 10 * 1024 * 1024)
        s3_repo.upload_video.side_effect = Exception("S3 upload failed")

        response = await use_case.execute([file], token="mock_token")

        assert "Erro: S3 upload failed" in response[0]["status"]

    async def test_execute_error_in_db_register(self, setup_use_case, mock_token_service, mock_upload_file):
        use_case, _, db_repo = setup_use_case
        mock_token_service.return_value = ("user@example.com", "12345")
        file = mock_upload_file("video.mp4", "video/mp4", 10 * 1024 * 1024)
        db_repo.register_video.side_effect = Exception("DB register failed")

        response = await use_case.execute([file], token="mock_token")

        assert "Erro: DB register failed" in response[0]["status"]

    async def test_execute_general_exception(self, setup_use_case, mock_token_service):
        use_case, _, _ = setup_use_case
        mock_token_service.side_effect = Exception("General error")

        with pytest.raises(HTTPException) as exc:
            await use_case.execute([], token="mock_token")

        assert exc.value.status_code == 500
        assert "General error" in exc.value.detail