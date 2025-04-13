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

    async def execute(self, files: UploadFile, token):
        setup_logging()
        logger = logging.getLogger(__name__)
        try:
            """ Processa o upload de vídeos, podendo rodar no modo simulado """

            user_email = TokenService.extract_user_email(token)

            if not user_email:
                logger.error("E-mail não encontrado no Token.")
                raise HTTPException(status_code=403, detail="E-mail não encontrado no Token")

            logger.info("Files recebidos para upload: %s", files)
            if not isinstance(files, list):
                files = [files]  # Wrap single file into a list
            if len(files) > 5:
                logger.error("Máximo de 5 vídeos permitidos.")
                raise HTTPException(status_code=400, detail="Máximo de 5 vídeos permitidos")

            video_responses = []

            for index, file in enumerate(files, start=1):
                try:
                    content = await file.read()
                    file_size = len(content)  # File size in bytes

                    # Validate file size (e.g., max 50MB)
                    max_size = 50 * 1024 * 1024  # 50MB
                    if file_size > max_size:
                        logger.error(f"Tamanho do vídeo {file.filename} excede 50MB.")
                        video_responses.append({
                            "video": f"Video {index}",
                            "details": f"Nome: {file.filename}, Tamanho: {file_size} bytes",
                            "status": "Erro: Tamanho máximo permitido é 50MB"
                        })
                        continue

                    video = Video(
                        file_name=file.filename,
                        file_size=file_size,
                        content=content,
                        user_email=user_email
                    )
                    logger.info(f"Processando vídeo: {video.file_name}")

                    s3_key = self.s3_repo.upload_video(video)
                    self.db_repo.register_video(video, s3_key)

                    video_responses.append({
                        "video": file.filename,
                        "details": f"Nome: {file.filename}, Tamanho: {file_size} bytes, Usuário: {user_email}",
                        "status": "Sucesso"
                    })

                except Exception as e:
                    logger.error(f"Erro ao processar o vídeo {file.filename}: {str(e)}")
                    video_responses.append({
                        "video": file.filename,
                        "details": f"Nome: {file.filename}, Tamanho: {file_size} bytes, Usuário: {user_email}",
                        "status": f"Erro: {str(e)}"
                    })

            return video_responses

        except HTTPException as e:
            raise HTTPException(e.status_code, e.detail)
        except Exception as e:
            logger.error(f"Erro ao processar o upload: {str(e)}")
            raise ValueError({f"Erro ao processar o upload: {str(e)}"})