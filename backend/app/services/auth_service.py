"""
Servicio de autenticación para el panel de administración.
Implementa JWT mínimo con HMAC-SHA256 usando solo la librería estándar de Python.
No requiere python-jose ni PyJWT.
"""
import base64
import hashlib
import hmac
import json
import logging
import time
from typing import Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

TOKEN_TYPE = "Bearer"
ALGORITHM = "HS256"


# ─────────────────────────────────────────────────────────────────────────────
#  Token helpers (stdlib HMAC-SHA256)
# ─────────────────────────────────────────────────────────────────────────────

def _b64_encode(data: bytes) -> str:
    """Base64url encode sin padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64_decode(s: str) -> bytes:
    """Base64url decode con padding dinámico."""
    padding = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (padding % 4))


def create_access_token(subject: str, extra: Optional[Dict[str, Any]] = None) -> str:
    """
    Genera un token JWT mínimo con:
    - header: {"alg": "HS256", "typ": "JWT"}
    - payload: {"sub": subject, "iat": now, "exp": now + expire, ...extra}
    - firma: HMAC-SHA256(header.payload, SECRET_KEY)
    """
    header = _b64_encode(json.dumps({"alg": ALGORITHM, "typ": "JWT"}).encode())
    now = int(time.time())
    payload_data: Dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + settings.JWT_EXPIRE_HOURS * 3600,
    }
    if extra:
        payload_data.update(extra)
    payload = _b64_encode(json.dumps(payload_data, separators=(",", ":")).encode())

    msg = f"{header}.{payload}"
    sig = _b64_encode(
        hmac.new(settings.SECRET_KEY.encode(), msg.encode(), hashlib.sha256).digest()
    )
    return f"{msg}.{sig}"


def verify_access_token(token: str) -> Dict[str, Any]:
    """
    Valida la firma y la expiración del token.
    Lanza ValueError si el token es inválido o expiró.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Formato de token inválido.")

        header_b64, payload_b64, sig_b64 = parts
        msg = f"{header_b64}.{payload_b64}"

        expected_sig = _b64_encode(
            hmac.new(settings.SECRET_KEY.encode(), msg.encode(), hashlib.sha256).digest()
        )
        # Comparación segura contra ataques de tiempo
        if not hmac.compare_digest(expected_sig, sig_b64):
            raise ValueError("Firma del token inválida.")

        payload = json.loads(_b64_decode(payload_b64))
        if payload.get("exp") and time.time() > payload["exp"]:
            raise ValueError("Token expirado.")

        return payload
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        raise ValueError(f"Token inválido: {exc}") from exc


# ─────────────────────────────────────────────────────────────────────────────
#  Validación de credenciales admin
# ─────────────────────────────────────────────────────────────────────────────

def authenticate_admin(email: str, password: str) -> Optional[str]:
    """
    Valida las credenciales contra las variables de entorno.
    Retorna el token JWT si son correctas, None si no.
    Usa hmac.compare_digest para evitar timing attacks.
    """
    email_ok = hmac.compare_digest(email.strip().lower(), settings.ADMIN_EMAIL.strip().lower())
    pass_ok = hmac.compare_digest(password, settings.ADMIN_PASSWORD)

    if email_ok and pass_ok:
        token = create_access_token(subject=email, extra={"role": "admin"})
        logger.info("Admin '%s' autenticado exitosamente.", email)
        return token

    logger.warning("Intento de autenticación fallido para '%s'.", email)
    return None
