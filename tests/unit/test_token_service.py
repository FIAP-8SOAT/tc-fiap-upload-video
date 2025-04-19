import unittest
from unittest.mock import patch, MagicMock
import jwt
from fastapi import HTTPException
from application.services.token_service import TokenService
import base64
import json


class TestTokenService(unittest.TestCase):

    def setUp(self):
        self.test_email = "test@example.com"
        self.valid_payload = {"email": self.test_email, "exp": 9999999999}
        self.expired_payload = {"email": self.test_email, "exp": 0}

        self.valid_token = self._generate_mock_jwt(self.valid_payload)
        self.expired_token = self._generate_mock_jwt(self.expired_payload)
        self.invalid_token = "invalid.token.here"

        self.logger_mock = MagicMock()

    def _generate_mock_jwt(self, payload):
        header = {"alg": "HS256", "typ": "JWT"}
        header_encoded = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        signature = base64.urlsafe_b64encode(b"signature").decode().rstrip("=")
        return f"{header_encoded}.{payload_encoded}.{signature}"

    @patch('os.getenv')
    @patch('jwt.decode')
    @patch('logging.getLogger')
    def test_extract_user_email_success(self, mock_get_logger, mock_decode, mock_getenv):
        mock_getenv.return_value = "secret_key"
        mock_decode.return_value = self.valid_payload
        mock_get_logger.return_value = self.logger_mock

        result = TokenService.extract_user_email_and_user_id(self.valid_token)

        self.assertEqual(result, self.test_email)
        mock_decode.assert_called_once()
        self.logger_mock.info.assert_called_once_with(f"Email extraído do token JWT: {self.test_email}")

    @patch('os.getenv')
    @patch('jwt.decode')
    @patch('logging.getLogger')
    def test_extract_user_email_missing_email(self, mock_get_logger, mock_decode, mock_getenv):
        mock_getenv.return_value = "secret_key"
        mock_decode.return_value = {}
        mock_get_logger.return_value = self.logger_mock

        with self.assertRaises(HTTPException) as context:
            TokenService.extract_user_email_and_user_id(self.valid_token)

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Erro ao obter email do Cognito", context.exception.detail)

    @patch('os.getenv')
    @patch('jwt.decode')
    @patch('logging.getLogger')
    def test_extract_user_email_expired_token(self, mock_get_logger, mock_decode, mock_getenv):
        mock_getenv.return_value = "secret_key"
        mock_decode.side_effect = jwt.ExpiredSignatureError("Token expired")
        mock_get_logger.return_value = self.logger_mock

        with self.assertRaises(HTTPException) as context:
            TokenService.extract_user_email_and_user_id(self.expired_token)

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Token expirado", context.exception.detail)

    @patch('os.getenv')
    @patch('jwt.decode')
    @patch('logging.getLogger')
    def test_extract_user_email_invalid_token(self, mock_get_logger, mock_decode, mock_getenv):
        mock_getenv.return_value = "secret_key"
        mock_decode.side_effect = jwt.InvalidTokenError("Invalid token")
        mock_get_logger.return_value = self.logger_mock

        with self.assertRaises(HTTPException) as context:
            TokenService.extract_user_email_and_user_id(self.invalid_token)

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Token inválido", context.exception.detail)

    @patch('os.getenv')
    @patch('jwt.decode')
    @patch('logging.getLogger')
    def test_extract_user_email_general_exception(self, mock_get_logger, mock_decode, mock_getenv):
        mock_getenv.return_value = "secret_key"
        mock_decode.side_effect = Exception("Some unexpected error")
        mock_get_logger.return_value = self.logger_mock

        with self.assertRaises(HTTPException) as context:
            TokenService.extract_user_email_and_user_id(self.valid_token)

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Erro ao processar Token", context.exception.detail)

    @patch('os.getenv')
    @patch('logging.getLogger')
    def test_extract_user_email_missing_secret_key(self, mock_get_logger, mock_getenv):
        mock_getenv.return_value = None
        mock_get_logger.return_value = self.logger_mock

        with self.assertRaises(HTTPException) as context:
            TokenService.extract_user_email_and_user_id(self.valid_token)

        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("Configuração SECRET_KEY não encontrada", context.exception.detail)

    @patch('os.getenv')
    @patch('logging.getLogger')
    def test_extract_user_email_empty_token(self, mock_get_logger, mock_getenv):
        mock_getenv.return_value = "secret_key"
        mock_get_logger.return_value = self.logger_mock

        with self.assertRaises(HTTPException) as context:
            TokenService.extract_user_email_and_user_id("")

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Token não fornecido", context.exception.detail)

    def _test_extract_user_email_and_user_id_invalid_token(self, token, mock_get_logger, mock_getenv):
        mock_getenv.return_value = "secret_key"
        mock_get_logger.return_value = self.logger_mock

        with self.assertRaises(HTTPException) as context:
            TokenService.extract_user_email_and_user_id(token)

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Token não fornecido", context.exception.detail)

    @patch('os.getenv')
    @patch('logging.getLogger')
    def test_extract_user_email_empty_token(self, mock_get_logger, mock_getenv):
        self._test_extract_user_email_and_user_id_invalid_token("", mock_get_logger, mock_getenv)

    @patch('os.getenv')
    @patch('logging.getLogger')
    def test_extract_user_email_and_user_id_none_token(self, mock_get_logger, mock_getenv):
        self._test_extract_user_email_and_user_id_invalid_token(None, mock_get_logger, mock_getenv)

    @patch('boto3.client')
    def test_get_email_from_cognito_success(self, mock_boto_client):
        mock_client = mock_boto_client.return_value
        mock_client.get_user.return_value = {
            'UserAttributes': [{'Name': 'email', 'Value': self.test_email}]
        }

        result = TokenService.get_email_from_cognito(self.valid_token)
        self.assertEqual(result, self.test_email)

    @patch('boto3.client')
    def test_get_email_from_cognito_failure(self, mock_boto_client):
        mock_client = mock_boto_client.return_value
        mock_client.get_user.side_effect = Exception("Invalid Access Token")

        with self.assertRaises(HTTPException) as context:
            TokenService.get_email_from_cognito(self.invalid_token)

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Erro ao obter email do Cognito", context.exception.detail)

    def test_decode_jwt_success(self):
        result = TokenService.decode_jwt(self.valid_token, "secret_key")
        self.assertEqual(result, self.valid_payload)

    def test_decode_jwt_invalid(self):
        with self.assertRaises(HTTPException) as context:
            TokenService.decode_jwt(self.invalid_token, "secret_key")

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Token inválido", context.exception.detail)

    @patch('jwt.PyJWKClient.get_signing_key_from_jwt')
    @patch('application.services.token_service.obter_user_pool_id')
    def test_extract_signature_success(self, mock_obter_user_pool_id, mock_get_signing_key):
        mock_obter_user_pool_id.return_value = "user_pool_id"
        mock_get_signing_key.return_value = "signing_key"

        result = TokenService.extract_signature(self.valid_token)
        self.assertEqual(result, "signing_key")
