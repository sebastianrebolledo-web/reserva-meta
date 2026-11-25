import logging
import uuid
from typing import Dict, Any, Optional
from googleapiclient.discovery import build
from app.core.config import settings
from app.services.google_auth import get_google_credentials
from app.schemas.reservation import ReservationCreate

logger = logging.getLogger(__name__)


def create_calendar_event(reservation: ReservationCreate) -> Dict[str, Any]:
    """
    Crea un evento de reserva en Google Calendar usando la API oficial v3.
    Si no hay credenciales configuradas, genera un ID simulado para pruebas locales.
    """
    creds = get_google_credentials()
    
    # Formateo del resumen y descripción
    equipment_lines = "\n".join(
        f"  - {item.quantity}x {item.name}" + (f" ({item.serial_or_notes})" if item.serial_or_notes else "")
        for item in reservation.equipment_details
    )

    description = (
        "=== RESERVA DE EQUIPOS META QUEST / OCULUS ===\n\n"
        f"• Solicitante: {reservation.applicant_email}\n"
        f"• KAM Responsable: {reservation.kam_name}\n"
        f"• Gerencia Comercial: {reservation.commercial_management}\n"
        f"• Cliente: {reservation.client_name}\n"
        f"• Período de Préstamo: {reservation.request_date.isoformat()} hasta {reservation.delivery_date.isoformat()} ({reservation.duration_days} días)\n\n"
        "• Equipos Solicitados:\n"
        f"{equipment_lines}\n\n"
        + (f"• Observaciones:\n  {reservation.notes}\n\n" if reservation.notes else "")
        + "Notificado a: " + settings.IT_SUPPORT_EMAIL
    )

    event_body = {
        "summary": f"Reserva Meta Quest - {reservation.client_name} ({reservation.kam_name})",
        "description": description,
        "start": {
            "dateTime": f"{reservation.request_date.isoformat()}T09:00:00",
            "timeZone": "America/Santiago",
        },
        "end": {
            "dateTime": f"{reservation.delivery_date.isoformat()}T18:00:00",
            "timeZone": "America/Santiago",
        },
        "attendees": [
            {"email": str(reservation.applicant_email)},
            {"email": settings.IT_SUPPORT_EMAIL},
        ],
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},  # 1 día antes
                {"method": "popup", "minutes": 60},       # 1 hora antes
            ],
        },
    }

    if not creds:
        mock_id = f"mock-cal-{uuid.uuid4().hex[:8]}"
        logger.info("[MODO SIMULACIÓN] Creando evento simulado en Google Calendar: %s", mock_id)
        return {
            "id": mock_id,
            "htmlLink": f"https://calendar.google.com/calendar/event?eid={mock_id}",
            "is_mock": True
        }

    try:
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        created_event = (
            service.events()
            .insert(calendarId=settings.GOOGLE_CALENDAR_ID, body=event_body)
            .execute()
        )
        logger.info("Evento creado con éxito en Google Calendar: %s", created_event.get("id"))
        return {
            "id": created_event.get("id"),
            "htmlLink": created_event.get("htmlLink"),
            "is_mock": False
        }
    except Exception as exc:
        logger.error("Error al crear evento en Google Calendar: %s", exc)
        raise RuntimeError(f"Error en Google Calendar API: {exc}") from exc
