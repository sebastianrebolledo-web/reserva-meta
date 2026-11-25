import logging
import random
import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.schemas.auth import (
    RequestUserCodeRequest,
    VerifyUserCodeRequest,
    UserAuthResponse,
)
from app.services.auth_service import create_access_token, verify_access_token
from app.services.google_gmail import send_user_otp_email

logger = logging.getLogger(__name__)
router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)

# Almacenamiento temporal en memoria de códigos OTP: email -> {"code": str, "expires_at": float}
_USER_OTP_STORE: Dict[str, Dict[str, Any]] = {}


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> Dict[str, Any]:
    """Valida el token si existe, o devuelve dict vacío si no se proporciona."""
    if not credentials:
        return {}
    try:
        return verify_access_token(credentials.credentials)
    except ValueError:
        return {}


def require_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> Dict[str, Any]:
    """Exige un token JWT válido de usuario o administrador."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación corporativa.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return verify_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/request-code",
    summary="Solicitar código de verificación para correo corporativo",
    description="Envía un código de 6 dígitos al correo corporativo para validar la identidad del colaborador.",
)
async def request_corporate_code(body: RequestUserCodeRequest) -> Dict[str, Any]:
    email_clean = body.email.strip().lower()

    # Generar código de 6 dígitos
    code = f"{random.randint(100000, 999999)}"
    _USER_OTP_STORE[email_clean] = {
        "code": code,
        "expires_at": time.time() + 600,  # 10 minutos
    }

    try:
        email_res = send_user_otp_email(email_clean, code)
        is_mock = email_res.get("is_mock", False)
        return {
            "success": True,
            "message": f"Código de seguridad enviado a tu casilla corporativa ({email_clean})",
            "is_mock": is_mock,
            "demo_code": code if is_mock else None,
        }
    except Exception as exc:
        logger.error("Error al enviar código de verificación corporativo: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo enviar el correo de verificación: {str(exc)}",
        )


@router.post(
    "/verify-code",
    response_model=UserAuthResponse,
    summary="Verificar código e iniciar sesión corporativa",
)
async def verify_corporate_code(body: VerifyUserCodeRequest) -> UserAuthResponse:
    email_clean = body.email.strip().lower()
    entry = _USER_OTP_STORE.get(email_clean)

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se ha solicitado ningún código o ya ha expirado.",
        )

    if time.time() > entry["expires_at"]:
        _USER_OTP_STORE.pop(email_clean, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de verificación ha expirado. Por favor solicita uno nuevo.",
        )

    if entry["code"] != body.code.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El código ingresado es incorrecto.",
        )

    # Código válido: consumir entrada
    _USER_OTP_STORE.pop(email_clean, None)
    
    # Determinar si es admin o usuario regular
    role = "admin" if email_clean == settings.ADMIN_EMAIL.strip().lower() else "user"
    token = create_access_token(subject=email_clean, extra={"role": role})
    logger.info("Colaborador corporativo '%s' autenticado exitosamente (rol: %s).", email_clean, role)

    return UserAuthResponse(
        access_token=token,
        token_type="Bearer",
        email=email_clean,
        role=role,
        expires_in_hours=settings.JWT_EXPIRE_HOURS,
    )


@router.get(
    "/me",
    summary="Obtener información del usuario autenticado",
)
async def get_authenticated_user(
    user_payload: Dict[str, Any] = Security(require_authenticated_user),
) -> Dict[str, Any]:
    return {
        "email": user_payload.get("sub"),
        "role": user_payload.get("role", "user"),
        "domain": settings.CORPORATE_DOMAIN,
    }
