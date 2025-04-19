import asyncio
import logging

from fastapi import HTTPException, UploadFile
from domain.entities.video import Video
from infrastructure.logging.logging_config import setup_logging
from application.services.token_service import TokenService
from adapters.repository.s3_repository import S3Repository
from adapters.repository.db_repository import DBRepository


class UploadVideoUseCase:
    def __init__(self, s3_repo: S3Repository, db_repo: DBRepository):
        self.s3_repo = s3_repo
        self.db_repo = db_repo
        setup_logging()
        self.logger = logging.getLogger(__name__)

    async def execute(self, files: list[UploadFile], token):
        try:
            user_email, user_id = TokenService.extract_user_email_and_user_id(token)

            if not user_email:
                self.logger.error("E-mail não encontrado no Token.")
                raise HTTPException(status_code=403, detail="E-mail não encontrado no Token")
            if not user_id:
                self.logger.error("Usuário não encontrado no Token.")
                raise HTTPException(status_code=403, detail="Usuário não encontrado no Token")

            self.logger.info("Files recebidos para upload: %s", files)
            if not isinstance(files, list):
                files = [files]
            if len(files) > 5:
                self.logger.error("Máximo de 5 vídeos permitidos.")
                raise HTTPException(status_code=400, detail="Máximo de 5 vídeos permitidos")
            if not files:
                self.logger.error("Não há arquivos para upload.")
                raise HTTPException(status_code=400, detail="Não há arquivos para upload.")

            async def process_video(file: UploadFile):
                global file_size
                try:
                    content = await file.read()
                    file_size = len(content)

                    max_size = 50 * 1024 * 1024  # 50MB
                    if file_size > max_size:
                        self.logger.error(f"Tamanho do vídeo {file.filename} excede 50MB.")
                        return {
                            "video": file.filename,
                            "details": f"Nome: {file.filename}, Tamanho: {(file_size / (1024 * 1024)):.2f} MB",
                            "status": "Erro: Tamanho máximo permitido é 50MB"
                        }

                    allowed_types = ["video/mp4", "video/mpeg", "video/quicktime"]
                    if file.content_type not in allowed_types:
                        self.logger.error(f"Tipo de mídia inválido: {file.content_type}")
                        return {
                            "video": file.filename,
                            "details": f"Nome: {file.filename}, Tamanho: {(file_size / (1024 * 1024)):.2f} MB",
                            "status": f"Erro: Tipo de mídia inválido: {file.content_type}"
                        }

                    video = Video(
                        file_name=file.filename,
                        file_size=file_size,
                        content=content,
                        user_email=user_email,
                        user_id=user_id
                    )

                    self.logger.info(f"Processando vídeo: {video.file_name}")
                    await self.s3_repo.upload_video(video)
                    await self.db_repo.register_video(video)

                    return {
                        "video": file.filename,
                        "details": f"Nome: {file.filename}, Tamanho: {(file_size / (1024 * 1024)):.2f} MB, Usuário: {user_email}",
                        "status": "Sucesso"
                    }

                except Exception as e:
                    self.logger.error(f"Erro ao processar o vídeo {file.filename}: {str(e)}")
                    return {
                        "video": file.filename,
                        "details": f"Nome: {file.filename}, Tamanho: {(file_size / (1024 * 1024)):.2f} MB, Usuário: {user_email}",
                        "status": f"Erro: {str(e)}"
                    }

            video_responses = await asyncio.gather(*[process_video(file) for file in files])

            return video_responses

        except HTTPException as http_exc:
            # Relevante para retornar o status code correto
            self.logger.error(f"Erro específico na execução do upload: {http_exc.detail}")
            raise http_exc
        except Exception as e:
            self.logger.error(f"Erro geral na execução do upload: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
