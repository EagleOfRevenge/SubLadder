import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from jose import jwt

from server.auth.jwt import _generate_jwt, _verify_jwt
from server.auth.routes import RegisterRequest, register


class ServerSecurityTests(unittest.TestCase):
    def test_verify_jwt_rejects_revoked_token(self):
        with patch("server.auth.jwt._load_config", return_value={"jwt": {"secret": "test-secret", "algorithm": "HS256", "expires_minutes": 60}}):
            token = _generate_jwt(42, "player@example.com", "Player")

        class DummyCursor:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def execute(self, *args, **kwargs):
                return None

            def fetchone(self):
                return {"jti": "revoked"}

        class DummyDB:
            def cursor(self, *args, **kwargs):
                return DummyCursor()

        with self.assertRaises(HTTPException) as ctx:
            _verify_jwt(token, db=DummyDB())

        self.assertEqual(ctx.exception.status_code, 401)

    def test_register_rejects_weak_payload(self):
        class DummyCursor:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def execute(self, *args, **kwargs):
                raise AssertionError("DB should not be touched for invalid input")

            def fetchone(self):
                return None

        class DummyDB:
            def cursor(self, *args, **kwargs):
                return DummyCursor()

            def commit(self):
                raise AssertionError("Commit should not happen")

        with self.assertRaises(Exception) as ctx:
            RegisterRequest(email="bad-email", password="short", game_name="ab")

        self.assertIn("validation", str(ctx.exception).lower())

    def test_generate_jwt_uses_environment_overrides(self):
        with patch("server.auth.jwt._load_config", return_value={"jwt": {"secret": "config-secret", "algorithm": "HS384", "expires_minutes": 10}}):
            with patch.dict(os.environ, {"JWT_SECRET": "env-secret", "JWT_ALGORITHM": "HS256", "JWT_EXPIRES_MINUTES": "30"}, clear=False):
                token = _generate_jwt(7, "player@example.com", "Player")

        payload = jwt.decode(token, "env-secret", algorithms=["HS256"])
        self.assertEqual(payload["sub"], "7")


if __name__ == "__main__":
    unittest.main()
