import unittest
from unittest.mock import patch, MagicMock
import jwt
from fastapi import HTTPException
from application.services.token_service import TokenService

class TestTokenService(unittest.TestCase):

    def setUp(self):
        self.valid_token = "valid.token.here"
        self.invalid_token = "invalid.token.here"
        self.expired_token = "expired.token.here"
        self.test_email = "test@example.com"
        self.valid_payload = {"email": self.test_email}
        self.logger_mock = MagicMock()

    @patch('os.getenv')
    @patch('jwt.decode')
    @patch('logging.getLogger')
    def test_extract_user_email_success(self, mock_get_logger, mock_decode, mock_getenv):
        """Testa extração de email com token válido"""
        mock_getenv.return_value = "secret_key"
        mock_decode.return_value = self.valid_payload
        mock_get_logger.return_value = self.logger_mock

        result = TokenService.extract_user_email(self.valid_token)

        self.assertEqual(result, self.test_email)
        mock_decode.assert_called_once_with(
            self.valid_token,
            key="secret_key",
            algorithms=["HS256"],
            options={'verify_signature': False, 'verify_exp': True, 'verify_iat': True}
        )
        self.logger_mock.info.assert_called_once_with(f"Email extraído do token JWT: {self.test_email}")

    @patch('os.getenv')
    @patch('jwt.decode')
    @patch('logging.getLogger')
    def test_extract_user_email_missing_email(self, mock_get_logger, mock_decode, mock_getenv):
        """Testa token válido mas sem campo email"""
        mock_getenv.return_value = "secret_key"
        mock_decode.return_value = {}  # Payload sem email
        mock_get_logger.return_value = self.logger_mock

        with self.assertRaises(HTTPException) as context:
            TokenService.extract_user_email(self.valid_token)

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Erro ao obter email do Cognito", context.exception.detail)

    @patch('os.getenv')
    @patch('jwt.decode')
    @patch('logging.getLogger')
    def test_extract_user_email_expired_token(self, mock_get_logger, mock_decode, mock_getenv):
        """Testa token expirado"""
        mock_getenv.return_value = "secret_key"
        mock_decode.side_effect = jwt.ExpiredSignatureError("Token expired")
        mock_get_logger.return_value = self.logger_mock

        with self.assertRaises(HTTPException) as context:
            TokenService.extract_user_email(self.expired_token)

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Token expirado", context.exception.detail)

    @patch('os.getenv')
    @patch('jwt.decode')
    @patch('logging.getLogger')
    def test_extract_user_email_invalid_token(self, mock_get_logger, mock_decode, mock_getenv):
        """Testa token inválido"""
        mock_getenv.return_value = "secret_key"
        mock_decode.side_effect = jwt.InvalidTokenError("Invalid token")
        mock_get_logger.return_value = self.logger_mock

        with self.assertRaises(HTTPException) as context:
            TokenService.extract_user_email(self.invalid_token)

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Token inválido", context.exception.detail)

    @patch('os.getenv')
    @patch('jwt.decode')
    @patch('logging.getLogger')
    def test_extract_user_email_general_exception(self, mock_get_logger, mock_decode, mock_getenv):
        """Testa outros erros genéricos"""
        mock_getenv.return_value = "secret_key"
        mock_decode.side_effect = Exception("Some unexpected error")
        mock_get_logger.return_value = self.logger_mock

        with self.assertRaises(HTTPException) as context:
            TokenService.extract_user_email(self.valid_token)

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Erro ao processar Token", context.exception.detail)

    @patch('os.getenv')
    @patch('jwt.decode')
    @patch('logging.getLogger')
    def test_extract_user_email_missing_secret_key(self, mock_get_logger, mock_decode, mock_getenv):
        """Testa quando SECRET_KEY não está configurada"""
        mock_getenv.return_value = None
        mock_get_logger.return_value = self.logger_mock

        with self.assertRaises(HTTPException) as context:
            TokenService.extract_user_email(self.valid_token)

        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("Configuração SECRET_KEY não encontrada", context.exception.detail)
        mock_decode.assert_not_called()

    @patch('os.getenv')
    @patch('jwt.decode')
    @patch('logging.getLogger')
    def test_extract_user_email_empty_token(self, mock_get_logger, mock_decode, mock_getenv):
        """Testa token vazio"""
        mock_getenv.return_value = "secret_key"
        mock_get_logger.return_value = self.logger_mock

        with self.assertRaises(HTTPException) as context:
            TokenService.extract_user_email("")

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Token não fornecido", context.exception.detail)
        mock_decode.assert_not_called()

    @patch('os.getenv')
    @patch('jwt.decode')
    @patch('logging.getLogger')
    def test_extract_user_email_none_token(self, mock_get_logger, mock_decode, mock_getenv):
        """Testa token None"""
        mock_getenv.return_value = "secret_key"
        mock_get_logger.return_value = self.logger_mock

        with self.assertRaises(HTTPException) as context:
            TokenService.extract_user_email("")

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("Token não fornecido", context.exception.detail)
        mock_decode.assert_not_called()