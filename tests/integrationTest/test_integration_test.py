import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from main import app
import os

@pytest.fixture
def mock_dependencies():
    with patch("main.S3Repository") as mock_s3, patch("main.DBRepository") as mock_db, patch("application.services.token_service.TokenService.extract_user_email") as mock_token:
        mock_s3.return_value.upload_video = AsyncMock(return_value="upload_success")
        mock_db.return_value.register_video = AsyncMock(return_value="register_success")
        mock_token.return_value = "test@example.com"
        yield mock_s3, mock_db, mock_token


@pytest.mark.asyncio
async def test_upload_com_arquivo_valido_e_token(mock_dependencies):
    async with AsyncClient(app=app, base_url="http://test") as client:
        with open("test_video.mp4", "wb") as f:
            f.write(b"fake mp4 content")
        with open("resources/videos_exemplos/natureza-00mm40ss.mp4", "rb") as file:
            response = await client.post(
                "/upload",
                headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
                                          ".eyJlbWFpbCI6InRlc3QyQGV4YW1wbGUuY29tLmJyIn0"
                                          ".iIs3H37n4faqte_ROGGAvyInxkSBynQkkXk1WSheHFQ"},
                files={"file": ("test_video.mp4", file, "video/mp4")}
            )
        assert response.status_code == 200
        assert response.json()["details"] == [{'details': 'Nome: test_video.mp4, Tamanho: 2045445 bytes, Usuário: test@example.com', 'status': 'Sucesso', 'video': 'test_video.mp4'}]
        #os.remove("test_video.mp4")


@pytest.mark.asyncio
async def test_upload_sem_token(mock_dependencies):
    async with AsyncClient(app=app, base_url="http://test") as client:
        with open("test_video.mp4", "wb") as f:
            f.write(b"fake mp4 content")
        with open("resources/videos_exemplos/natureza-00mm40ss.mp4", "rb") as file:
            response = await client.post(
                "/upload",
                files={"file": ("test_video.mp4", file, "video/mp4")}
            )
        assert response.status_code == 401
        assert response.json()["detail"] == "Token inválido"
        os.remove("test_video.mp4")


@pytest.mark.asyncio
async def test_upload_com_formato_invalido(mock_dependencies):
    async with AsyncClient(app=app, base_url="http://test") as client:
        with open("teste.txt", "w") as f:
            f.write("isso nao é um video")
        with open("teste.txt", "rb") as file:
            response = await client.post(
                "/upload",
                headers={"Authorization": "Bearer valid_token"},
                files={"file": ("teste.txt", file, "text/plain")}
            )
        assert response.status_code == 400
        os.remove("teste.txt")


@pytest.mark.asyncio
async def test_upload_com_multiplos_arquivos(mock_dependencies):
    async with AsyncClient(app=app, base_url="http://test") as client:
        with open("video1.mp4", "wb") as f:
            f.write(b"video 1")
        with open("video2.mp4", "wb") as f:
            f.write(b"video 2")
        with open("video1.mp4", "rb") as f1, open("video2.mp4", "rb") as f2:
            response = await client.post(
                "/upload",
                headers={"Authorization": "Bearer valid_token"},
                files=[
                    ("file", ("video1.mp4", f1, "video/mp4")),
                    ("file", ("video2.mp4", f2, "video/mp4"))
                ]
            )
        assert response.status_code == 200
        os.remove("video1.mp4")
        os.remove("video2.mp4")


@pytest.mark.asyncio
async def test_upload_sem_arquivo(mock_dependencies):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/upload",
            headers={"Authorization": "Bearer valid_token"},
            files={}
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_com_nome_de_arquivo_ausente(mock_dependencies):
    async with AsyncClient(app=app, base_url="http://test") as client:
        with open("file.mp4", "wb") as f:
            f.write(b"video")
        with open("file.mp4", "rb") as file:
            response = await client.post(
                "/upload",
                headers={"Authorization": "Bearer valid_token"},
                files={"file": ("", file, "video/mp4")}
            )
        assert response.status_code == 400
        os.remove("file.mp4")


@pytest.mark.asyncio
async def test_upload_com_tipo_de_midia_ausente(mock_dependencies):
    async with AsyncClient(app=app, base_url="http://test") as client:
        with open("file.mp4", "wb") as f:
            f.write(b"video")
        with open("file.mp4", "rb") as file:
            response = await client.post(
                "/upload",
                headers={"Authorization": "Bearer valid_token"},
                files={"file": ("file.mp4", file)}
            )
        assert response.status_code == 400
        os.remove("file.mp4")