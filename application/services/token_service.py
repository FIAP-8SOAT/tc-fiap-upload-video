import logging
import os

from fastapi import HTTPException

import jwt

from infrastructure.logging.logging_config import setup_logging


class TokenService:
    @staticmethod
    def extract_user_email(token: str) -> str:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)

        if not token:
            raise HTTPException(status_code=401, detail="Token não fornecido")

        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            raise HTTPException(status_code=500, detail="Configuração SECRET_KEY não encontrada")

        try:
            decoded_token = jwt.decode(
                token,
                key=secret_key,
                algorithms=["HS256"],
                options={"verify_signature": False}
            )

            logger.info(f"Decoded token: {decoded_token}")

            email = decoded_token.get("email")
            if not email:
                raise HTTPException(status_code=401, detail="Email não encontrado no token")

            return email

        except jwt.ExpiredSignatureError as e:
            raise HTTPException(status_code=401, detail="Token expirado: " + str(e))
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail="Token inválido: " + str(e))
        except Exception as e:
            raise HTTPException(status_code=401, detail="Erro ao processar Token: " + str(e))
