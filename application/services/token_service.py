import logging
import os
from typing import Any, Tuple

import boto3
import botocore
import jwt
from fastapi import HTTPException
from jwt import PyJWKClient

from infrastructure.logging.logging_config import setup_logging


def obter_user_pool_id() -> str:
    try:
        client = boto3.client('cognito-idp', region_name=os.getenv("REGION_NAME"))
        response = client.list_user_pools(MaxResults=1)

        user_pools = response.get("UserPools", [])
        if not user_pools:
            return None

        return user_pools[0]["Id"]

    except botocore.exceptions.BotoCoreError as e:
        print(f"Erro ao acessar Cognito: {e}")
    return None


class TokenService:

    @staticmethod
    def get_email_from_cognito(access_token: str) -> str:
        """
        Recupera o email do usuário a partir do Cognito utilizando o token de acesso.
        """
        try:
            client = boto3.client('cognito-idp', region_name=os.getenv("REGION_NAME"))
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
                options={"verify_signature": False},
            )
            return decoded_token
        except jwt.ExpiredSignatureError as e:
            raise HTTPException(status_code=401, detail=f"Token expirado: {str(e)}")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Erro ao processar Token: {str(e)}")

    @staticmethod
    def extract_user_email_and_user_id(token: str) -> tuple[str, str] | Any:
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
        user_id = decoded_token.get("client_id", None);
        logging.info(f"User_id extraído do token JWT: {user_id}")
        if not email_retry:
            raise HTTPException(status_code=401, detail="Email não encontrado no token nem no Cognito")

        logger.info(f"Email extraído do Cognito: {email_retry}")
        logger.info(f"User_id extraído do Cognito: {user_id}")
        return email_retry, user_id

    @staticmethod
    def extract_signature(token: str) -> str:
        user_pool_id = obter_user_pool_id()
        # URL do JWKS do seu User Pool
        jwks_url = f"https://cognito-idp.{os.getenv('REGION_NAME')}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"

        # Pega a chave pública correta com base no 'kid' do token
        jwks_client = PyJWKClient(jwks_url)
        return jwks_client.get_signing_key_from_jwt(token);

