import logging
from fastapi import HTTPException

import jwt

from infrastructure.logging.logging_config import setup_logging


class TokenService:
    @staticmethod
    def extract_user_email(token: str) -> str:
        """ Extrai e valida o token JWT para obter o email do usuário """
        try:
            # Setup logging
            setup_logging()
            logger = logging.getLogger(__name__)

            decoded_token = jwt.decode(
                token,
                key="your_secret_key",
                algorithms=["HS256"],
                options={"verify_signature": True}
            )
            # Log the decoded token for debugging
            logger.info(f"Decoded token: {decoded_token}")

            return decoded_token.get("email")
        except jwt.ExpiredSignatureError as e:
            raise HTTPException(status_code=401, detail="Token expirado: " + str(e))
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail="Token inválido: " + str(e))
        except Exception as e:
            raise HTTPException(status_code=401, detail="Erro ao processar Token: " + str(e))
