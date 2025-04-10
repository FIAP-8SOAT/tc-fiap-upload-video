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

    async def execute(self, files: UploadFile, token, simulate=True):
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

            uploaded_videos = []

            for file in files:
                video = Video(
                    file_name=file.filename,  # Access filename attribute
                    file_size=file.spool_max_size,  # Access file size attribute
                    content=await file.read(),  # Read file content
                    user_email=user_email
                )
                logger.info(f"Processando vídeo: {video.file_name}")

                if video.file_size > (50 * 1024 * 1024):  # Máx 50MB
                    raise HTTPException(status_code=400, detail="Tamanho máximo permitido é 50MB")

                if simulate:
                    uploaded_videos.append({
                        "user_email": video.user_email,
                        "file_name": video.file_name,
                        "size": video.file_size
                    })
                else:
                    s3_key = self.s3_repo.upload_video(video)
                    self.db_repo.register_video(video, s3_key)
                    uploaded_videos.append(s3_key)

            return {"message": "Upload concluído", "videos": uploaded_videos}, 200

        except HTTPException as e:
            raise HTTPException(e.status_code, e.detail)
        except Exception as e:
            logger.error(f"Erro ao processar o upload: {str(e)}")
            raise ValueError({f"Erro ao processar o upload: {str(e)}"})