import unittest
import asyncio
from app.schemas.auth import RequestUserCodeRequest, VerifyUserCodeRequest
from app.api.v1.endpoints.auth import (
    request_corporate_code,
    verify_corporate_code,
    _USER_OTP_STORE,
)
from pydantic import ValidationError


class TestCorporateAuth(unittest.TestCase):
    def setUp(self):
        _USER_OTP_STORE.clear()

    def test_corporate_email_domain_validation(self):
        # Correo corporativo válido
        req = RequestUserCodeRequest(email="colaborador@grupotecfluid.com")
        self.assertEqual(req.email, "colaborador@grupotecfluid.com")

        # Correo no corporativo debe fallar en validación Pydantic
        with self.assertRaises(ValidationError):
            RequestUserCodeRequest(email="externo@gmail.com")

        with self.assertRaises(ValidationError):
            RequestUserCodeRequest(email="otro@otraempresa.cl")

    def test_request_and_verify_code_flow(self):
        # 1. Solicitar código
        req = RequestUserCodeRequest(email="juan.perez@grupotecfluid.com")
        res = asyncio.run(request_corporate_code(req))
        self.assertTrue(res["success"])
        self.assertIn("juan.perez@grupotecfluid.com", _USER_OTP_STORE)

        saved_code = _USER_OTP_STORE["juan.perez@grupotecfluid.com"]["code"]
        self.assertEqual(len(saved_code), 6)

        # 2. Código incorrecto debe fallar
        verify_bad = VerifyUserCodeRequest(
            email="juan.perez@grupotecfluid.com",
            code="000000" if saved_code != "000000" else "111111"
        )
        with self.assertRaises(Exception):
            asyncio.run(verify_corporate_code(verify_bad))

        # 3. Código correcto debe emitir token
        verify_ok = VerifyUserCodeRequest(
            email="juan.perez@grupotecfluid.com",
            code=saved_code
        )
        auth_res = asyncio.run(verify_corporate_code(verify_ok))
        self.assertEqual(auth_res.email, "juan.perez@grupotecfluid.com")
        self.assertEqual(auth_res.token_type, "Bearer")
        self.assertTrue(len(auth_res.access_token) > 20)
        self.assertEqual(auth_res.role, "user")


if __name__ == "__main__":
    unittest.main()
