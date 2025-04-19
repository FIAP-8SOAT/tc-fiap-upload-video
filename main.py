import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Header, HTTPException, Request
from mangum import Mangum

from application.use_cases.upload_video import UploadVideoUseCase
from infrastructure.logging.logging_config import setup_logging
from adapters.repository.s3_repository import S3Repository
from adapters.repository.db_repository import DBRepository

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup: Initializing resources.")
    yield
    logger.info("Application shutdown: Cleaning up resources.")

app = FastAPI(lifespan=lifespan)


@app.post("/upload")
async def upload_file(
        request: Request,
        file: list[UploadFile] = File(...),
        authorization: str = Header(...)
):
    try:
        if not authorization.startswith("Bearer "):
            logger.warning("Invalid token format.")
            raise HTTPException(status_code=401, detail="Token inválido")

        if not request.headers.get("content-type", "").startswith("multipart/form-data"):
            raise HTTPException(status_code=400, detail="Requisição deve ser multipart/form-data")

        s3_repo = S3Repository("fiapeats-bucket-videos-s3")
        db_repo = DBRepository("fiapeatsdb")
        upload_video_use_case = UploadVideoUseCase(s3_repo, db_repo)

        token = authorization.split("Bearer ")[1]

        result = await upload_video_use_case.execute(file, token)
        return {"details": result}

    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid data format.")
    except Exception as e:
        logger.error(f"Error during upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error.")

# Adaptador para Lambda
handler = Mangum(app)