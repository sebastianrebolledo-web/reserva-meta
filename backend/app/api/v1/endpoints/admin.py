"""
Endpoints del Panel de Administración.
Rutas protegidas con Bearer JWT (HMAC-SHA256, stdlib).
"""
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Response, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db import crud
import json
import random
import time
from datetime import date

from app.db import crud
from app.schemas.admin import (
    AdminLoginRequest,
    AdminLoginResponse,
    UpdateEstadoRequest,
    RequestCodeRequest,
    VerifyCodeRequest,
)
from app.services.auth_service import authenticate_admin, verify_access_token, create_access_token
from app.services.google_gmail import send_admin_otp_email
from app.services.acta_generator import generate_acta_pdf
from app.schemas.reservation import EquipmentItem, ReservationCreate
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
bearer_scheme = HTTPBearer()

# Almacenamiento temporal de códigos OTP: email -> {"code": str, "expires_at": float}
_ADMIN_OTP_STORE: Dict[str, Dict[str, Any]] = {}


# ─────────────────────────────────────────────────────────────────────────────
#  Dependency: verificar token en cada ruta protegida
# ─────────────────────────────────────────────────────────────────────────────

def require_admin(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> Dict[str, Any]:
    try:
        payload = verify_access_token(credentials.credentials)
        if payload.get("role") != "admin":
            raise ValueError("Rol insuficiente.")
        return payload
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Autenticación
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/request-code",
    summary="Solicitar código de verificación enviado a Gmail",
)
async def request_admin_code(body: RequestCodeRequest) -> Dict[str, Any]:
    email_clean = body.email.strip().lower()

    # Validar que el correo pertenezca al administrador configurado o soporte TI
    authorized_admins = [
        settings.ADMIN_EMAIL.strip().lower(),
        *[e.lower() for e in settings.it_support_recipients],
    ]
    if email_clean not in authorized_admins:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este correo no está registrado con privilegios de administrador TI.",
        )

    # Generar código de 6 dígitos
    code = f"{random.randint(100000, 999999)}"
    _ADMIN_OTP_STORE[email_clean] = {
        "code": code,
        "expires_at": time.time() + 600,  # 10 minutos
    }

    try:
        email_res = send_admin_otp_email(email_clean, code)
        is_mock = email_res.get("is_mock", False)
        return {
            "success": True,
            "message": f"Código enviado exitosamente a tu cuenta de Gmail ({email_clean})",
            "is_mock": is_mock,
            "demo_code": code if is_mock else None,
        }
    except Exception as exc:
        logger.error("Error al enviar código a Gmail: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo enviar el correo de verificación: {str(exc)}",
        )


@router.post(
    "/verify-code",
    response_model=AdminLoginResponse,
    summary="Verificar código de Gmail e iniciar sesión",
)
async def verify_admin_code(body: VerifyCodeRequest) -> AdminLoginResponse:
    email_clean = body.email.strip().lower()
    entry = _ADMIN_OTP_STORE.get(email_clean)

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se ha solicitado ningún código o ya ha expirado.",
        )

    if time.time() > entry["expires_at"]:
        _ADMIN_OTP_STORE.pop(email_clean, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de verificación ha expirado. Solicita uno nuevo.",
        )

    if entry["code"] != body.code.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El código ingresado es incorrecto.",
        )

    # Código válido: consumir y retornar token
    _ADMIN_OTP_STORE.pop(email_clean, None)
    token = create_access_token(subject=email_clean, extra={"role": "admin"})
    logger.info("Admin '%s' autenticado exitosamente mediante Gmail.", email_clean)

    return AdminLoginResponse(
        access_token=token,
        token_type="Bearer",
        expires_in_hours=settings.JWT_EXPIRE_HOURS,
    )


@router.post(
    "/login",
    response_model=AdminLoginResponse,
    summary="Autenticar al administrador mediante contraseña maestra",
)
async def admin_login(body: AdminLoginRequest) -> AdminLoginResponse:
    token = authenticate_admin(body.email, body.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AdminLoginResponse(
        access_token=token,
        token_type="Bearer",
        expires_in_hours=settings.JWT_EXPIRE_HOURS,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  KPIs y Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/kpis",
    summary="Indicadores clave del inventario y solicitudes",
    dependencies=[Depends(require_admin)],
)
async def get_kpis() -> Dict[str, Any]:
    return crud.get_kpi_summary()


@router.get(
    "/solicitudes",
    summary="Listar todas las solicitudes de reserva",
    dependencies=[Depends(require_admin)],
)
async def list_solicitudes() -> List[Dict[str, Any]]:
    return crud.get_all_solicitudes()


@router.get(
    "/solicitudes/{solicitud_id}",
    summary="Obtener una solicitud por ID",
    dependencies=[Depends(require_admin)],
)
async def get_solicitud(solicitud_id: int) -> Dict[str, Any]:
    sol = crud.get_solicitud_by_id(solicitud_id)
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
    return sol


@router.patch(
    "/solicitudes/{solicitud_id}/estado",
    summary="Cambiar el estado de una solicitud",
    dependencies=[Depends(require_admin)],
)
async def update_estado(solicitud_id: int, body: UpdateEstadoRequest) -> Dict[str, Any]:
    updated = crud.update_solicitud_estado(solicitud_id, body.estado)
    if not updated:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
    return updated


# ─────────────────────────────────────────────────────────────────────────────
#  Descarga del Acta PDF
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/solicitudes/{solicitud_id}/acta",
    summary="Descargar Acta de Préstamo en PDF",
    dependencies=[Depends(require_admin)],
    response_class=Response,
)
async def download_acta(solicitud_id: int) -> Response:
    sol = crud.get_solicitud_by_id(solicitud_id)
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")

    # Reconstruir el esquema de ReservationCreate desde el registro BD
    equipment = [
        EquipmentItem(**item) if isinstance(item, dict) else item
        for item in sol["equipment_details"]
    ]
    reservation = ReservationCreate(
        applicant_email=sol["applicant_email"],
        kam_name=sol["kam_name"],
        commercial_management=sol["commercial_management"],
        client_name=sol["client_name"],
        request_date=date.fromisoformat(sol["request_date"]),
        duration_days=sol["duration_days"],
        equipment_details=equipment,
        notes=sol.get("notes") or "",
    )

    pdf_bytes = generate_acta_pdf(reservation)
    filename = f"Acta_{sol['folio']}_{sol['client_name'].replace(' ', '_')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Inventario
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/inventario",
    summary="Listar inventario de equipos",
    dependencies=[Depends(require_admin)],
)
async def list_inventory() -> List[Dict[str, Any]]:
    return crud.get_all_inventory()
