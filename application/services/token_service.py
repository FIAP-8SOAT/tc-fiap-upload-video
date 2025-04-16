import logging
import os
import boto3
import jwt
from fastapi import HTTPException
from infrastructure.logging.logging_config import setup_logging


class TokenService:

    @staticmethod
    def get_email_from_cognito(access_token: str) -> str:
        """
        Recupera o email do usuário a partir do Cognito utilizando o token de acesso.
        """
        try:
            client = boto3.client('cognito-idp', region_name='us-east-1')
            response = client.get_user(AccessToken=access_token)
            return next(attr['Value'] for attr in response['UserAttributes'] if attr['Name'] == 'email')
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Erro ao obter email do Cognito: {str(e)}")

    @staticmethod
    def decode_jwt(token: str, secret_key: str):
        """
        Decodifica o JWT utilizando a chave secreta e valida sua assinatura.
        """
        try:
            decoded_token = jwt.decode(
                token,
                key=secret_key,
                algorithms=["HS256"],
                options={"verify_signature": False, "verify_exp": True, "verify_iat": True},
            )
            return decoded_token
        except jwt.ExpiredSignatureError as e:
            raise HTTPException(status_code=401, detail=f"Token expirado: {str(e)}")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Erro ao processar Token: {str(e)}")

    @staticmethod
    def extract_user_email(token: str) -> str:
        """
        Extrai o email do token JWT ou, caso não presente, recupera-o a partir do Cognito.
        """
        # Setup de log
        setup_logging()
        logger = logging.getLogger(__name__)

        if not token:
            raise HTTPException(status_code=401, detail="Token não fornecido")

        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            raise HTTPException(status_code=500, detail="Configuração SECRET_KEY não encontrada")

        # Primeira tentativa: Decodificar o JWT
        decoded_token = TokenService.decode_jwt(token, secret_key)

        email = decoded_token.get("email")
        if email:
            logger.info(f"Email extraído do token JWT: {email}")
            return email

        # Se o e-mail não estiver no JWT, tentamos buscar via Cognito
        logger.info("Email não encontrado no token, tentando buscar via Cognito.")
        email_retry = TokenService.get_email_from_cognito(token)
        if not email_retry:
            raise HTTPException(status_code=401, detail="Email não encontrado no token nem no Cognito")

        logger.info(f"Email extraído do Cognito: {email_retry}")
        return email_retry
