import logging

from fastapi import FastAPI, File, UploadFile, Header, HTTPException
from application.use_cases.upload_video import UploadVideoUseCase
from infrastructure.logging.logging_config import setup_logging
from adapters.repository.s3_repository import S3Repository
from adapters.repository.db_repository import DBRepository

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    logger.info("Application startup: Initializing resources.")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Application shutdown: Cleaning up resources.")

@app.post("/upload")
async def upload_file(
        file: list[UploadFile] = File(...),
        authorization: str = Header(...)
):
    s3_repo = S3Repository("fiapeats-bucket-s3")
    db_repo = DBRepository("table_name_test")
    upload_video_use_case = UploadVideoUseCase(s3_repo, db_repo)

    # Extração e validação do token
    if not authorization.startswith("Bearer "):
        logger.warning("Invalid token format.")
        raise HTTPException(status_code=401, detail="Token inválido")

    token = authorization.split("Bearer ")[1]

    # Chama o caso de uso de upload
    try:
        result = await upload_video_use_case.execute(file, token)
        return {"details": result}

    except HTTPException as e:
        raise HTTPException(e.status_code, e.detail)
    except Exception as e:
        logger.error(f"Error during upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"{str(e)}")