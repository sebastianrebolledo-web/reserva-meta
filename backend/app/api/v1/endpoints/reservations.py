import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, Response

from app.schemas.reservation import ReservationCreate, ReservationResponse
from app.services.google_calendar import create_calendar_event
from app.services.google_gmail import send_reservation_email
from app.services.acta_generator import generate_acta_html, generate_acta_pdf
from app.api.v1.endpoints.auth import get_current_user_optional
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear solicitud de reserva de equipos Meta Quest",
    description=(
        "Valida los datos corporativos, programa el evento en Google Calendar, "
        "genera el Acta de Préstamo en PDF y notifica por Gmail al solicitante y a Soporte TI."
    )
)
async def create_reservation(
    reservation: ReservationCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_optional),
) -> ReservationResponse:
    # Si viene con sesión autenticada, verificar que coincida con el solicitante (salvo admin)
    if isinstance(current_user, dict) and current_user and current_user.get("role") != "admin":
        auth_email = current_user.get("sub", "").lower()
        req_email = reservation.applicant_email.lower()
        if auth_email and auth_email != req_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tu sesión autenticada ({auth_email}) no coincide con el correo solicitante ({req_email}).",
            )
    try:


        # 1. Crear evento en Google Calendar
        calendar_result = create_calendar_event(reservation)
        event_id = calendar_result.get("id")
        event_link = calendar_result.get("htmlLink")

        # 2. Enviar correo con Acta PDF adjunta vía Gmail API
        email_result = send_reservation_email(
            reservation,
            calendar_link=event_link,
            include_acta_pdf=True,
        )
        email_sent = email_result.get("sent", False)

        # 3. Guardar registro en la base de datos local SQLite
        try:
            from app.db import crud
            crud.create_solicitud({
                "applicant_email": str(reservation.applicant_email),
                "kam_name": reservation.kam_name,
                "commercial_management": reservation.commercial_management,
                "client_name": reservation.client_name,
                "request_date": reservation.request_date,
                "duration_days": reservation.duration_days,
                "delivery_date": reservation.delivery_date,
                "equipment_details": [
                    item.model_dump() if hasattr(item, "model_dump") else item.dict()
                    for item in reservation.equipment_details
                ],
                "notes": reservation.notes or "",
                "event_id": event_id or "",
                "event_link": event_link or "",
            })
        except Exception as db_err:
            logger.error("Error al persistir solicitud en base de datos: %s", db_err)

        # 4. Resumen descriptivo de los equipos
        equipment_summary = ", ".join(
            f"{item.quantity}x {item.name}" for item in reservation.equipment_details
        )

        return ReservationResponse(
            success=True,
            message="Reserva creada. Acta de Préstamo generada y enviada exitosamente.",
            event_id=event_id,
            event_link=event_link,
            email_notification_sent=email_sent,
            applicant_email=reservation.applicant_email,
            kam_name=reservation.kam_name,
            client_name=reservation.client_name,
            request_date=reservation.request_date,
            duration_days=reservation.duration_days,
            delivery_date=reservation.delivery_date,
            equipment_summary=equipment_summary,
        )

    except ValueError as val_err:
        logger.warning("Error de validación en la reserva: %s", val_err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as exc:
        logger.error("Error al procesar la reserva: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo completar la reserva de equipos: {str(exc)}"
        )


@router.post(
    "/acta/pdf",
    summary="Previsualizar Acta de Préstamo en PDF",
    description="Genera y descarga el PDF del Acta de Préstamo en base a los datos del formulario, sin crear el evento ni enviar correo.",
    response_class=Response,
)
async def preview_acta_pdf(reservation: ReservationCreate) -> Response:
    try:
        pdf_bytes = generate_acta_pdf(reservation)
        filename = (
            f"Acta_Prestamo_MetaQuest_{reservation.client_name.replace(' ', '_')}_"
            f"{reservation.request_date.strftime('%Y%m%d')}.pdf"
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes)),
            },
        )
    except Exception as exc:
        logger.error("Error generando PDF del Acta: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar el Acta PDF: {str(exc)}"
        )


@router.post(
    "/acta/html",
    summary="Previsualizar Acta de Préstamo en HTML",
    description="Renderiza el Acta de Préstamo en formato HTML para previsualización en navegador.",
    response_class=HTMLResponse,
)
async def preview_acta_html(reservation: ReservationCreate) -> HTMLResponse:
    try:
        html = generate_acta_html(reservation)
        return HTMLResponse(content=html, status_code=200)
    except Exception as exc:
        logger.error("Error generando HTML del Acta: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar el Acta HTML: {str(exc)}"
        )


@router.get(
    "/health",
    summary="Verificar estado de la API de Reservas",
    description="Permite al frontend comprobar conectividad y la configuración corporativa.",
)
async def get_health_status():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "corporate_domain": settings.CORPORATE_DOMAIN,
        "it_support_emails": settings.it_support_recipients,
        "auth_mode": settings.GOOGLE_AUTH_MODE,
        "features": ["calendar", "gmail", "acta_pdf"],
    }
