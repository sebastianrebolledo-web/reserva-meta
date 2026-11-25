import base64
import logging
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional
from googleapiclient.discovery import build
from app.core.config import settings
from app.services.google_auth import get_google_credentials
from app.services.acta_generator import generate_acta_html, generate_acta_pdf
from app.schemas.reservation import ReservationCreate

logger = logging.getLogger(__name__)


def send_reservation_email(
    reservation: ReservationCreate,
    calendar_link: str = "",
    include_acta_pdf: bool = True,
) -> Dict[str, Any]:
    """
    Envía un correo completo al solicitante y a soporte TI con:
    - Resumen de la reserva en formato HTML.
    - Acta de Préstamo generada como adjunto PDF.
    - Acta de Préstamo en cuerpo HTML alternativo (fallback visual).
    
    Utiliza Gmail API v1 y los módulos estándar email.mime de Python.
    """
    creds = get_google_credentials()

    subject = f"[Reserva Meta Quest] Acta de Préstamo – {reservation.client_name} ({reservation.request_date.strftime('%d/%m/%Y')})"

    # Generar el Acta en ambos formatos
    acta_html = generate_acta_html(reservation)
    acta_pdf_bytes: Optional[bytes] = None
    if include_acta_pdf:
        try:
            acta_pdf_bytes = generate_acta_pdf(reservation)
        except Exception as exc:
            logger.warning("No se pudo generar el PDF del acta: %s. Se enviará solo el HTML.", exc)

    # Resumen del equipamiento
    equipment_rows_html = "".join(
        f"<tr><td style='padding:8px 12px;border-bottom:1px solid #e2e8f0;'>{item.name}</td>"
        f"<td style='padding:8px 12px;border-bottom:1px solid #e2e8f0;text-align:center;'>{item.quantity}</td>"
        f"<td style='padding:8px 12px;border-bottom:1px solid #e2e8f0;'>{item.serial_or_notes or '-'}</td></tr>"
        for item in reservation.equipment_details
    )

    equipment_text = "\n".join(
        f"  - {item.quantity}x {item.name}" + (f" ({item.serial_or_notes})" if item.serial_or_notes else "")
        for item in reservation.equipment_details
    )

    support_emails_str = ", ".join(settings.it_support_recipients)

    # ─────────────────────────────────────────────────────────────
    #  CUERPO DEL CORREO: Notificación de Reserva + Acta adjunta
    # ─────────────────────────────────────────────────────────────
    notification_html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
                 line-height:1.6;color:#1e293b;background-color:#f8fafc;padding:24px;">
      <div style="max-width:640px;margin:0 auto;background:#ffffff;border:1px solid #e2e8f0;
                  border-radius:12px;overflow:hidden;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">

        <!-- Header -->
        <div style="background:#0f172a;padding:24px 28px;border-bottom:3px solid #024c80;">
          <p style="color:#94a3b8;font-size:12px;margin:0 0 4px;text-transform:uppercase;letter-spacing:0.5px;">
            Grupo Tecfluid — Sistema de Reservas
          </p>
          <h2 style="color:#ffffff;margin:0;font-size:19px;font-weight:700;">
            Acta de Préstamo de Visores Meta Quest
          </h2>
        </div>

        <div style="padding:24px 32px;">
          <p style="font-size:15px;color:#334155;margin-top:0;">
            Estimado/a <strong>{reservation.kam_name}</strong>,<br>
            Se ha generado y adjunta el <strong>Acta de Préstamo oficial</strong> para la siguiente solicitud de equipamiento de Realidad Virtual:
          </p>

          <!-- Datos principales -->
          <table style="width:100%;border-collapse:collapse;font-size:14px;margin:20px 0;background:#f1f5f9;border-radius:8px;">
            <tr><td style="padding:7px 14px;font-weight:600;width:42%;color:#475569;">KAM Responsable:</td>
                <td style="padding:7px 14px;font-weight:700;">{reservation.kam_name}</td></tr>
            <tr style="background:#e8f0fe20;"><td style="padding:7px 14px;font-weight:600;color:#475569;">Gerencia Comercial:</td>
                <td style="padding:7px 14px;">{reservation.commercial_management}</td></tr>
            <tr><td style="padding:7px 14px;font-weight:600;color:#475569;">Correo Solicitante:</td>
                <td style="padding:7px 14px;">{reservation.applicant_email}</td></tr>
            <tr style="background:#e8f0fe20;"><td style="padding:7px 14px;font-weight:600;color:#475569;">Cliente:</td>
                <td style="padding:7px 14px;font-weight:700;">{reservation.client_name}</td></tr>
            <tr><td style="padding:7px 14px;font-weight:600;color:#475569;">Fecha de entrega (inicio):</td>
                <td style="padding:7px 14px;">{reservation.request_date.strftime('%d/%m/%Y')}</td></tr>
            <tr style="background:#e8f0fe20;"><td style="padding:7px 14px;font-weight:600;color:#475569;">Días de préstamo:</td>
                <td style="padding:7px 14px;">{reservation.duration_days} días</td></tr>
            <tr><td style="padding:7px 14px;font-weight:700;color:#024c80;font-size:15px;">Fecha de devolución:</td>
                <td style="padding:7px 14px;font-weight:800;color:#024c80;font-size:15px;">
                  {reservation.delivery_date.strftime('%d/%m/%Y')}</td></tr>
          </table>

          <!-- Equipos -->
          <h3 style="font-size:15px;margin:20px 0 10px;color:#0f172a;border-bottom:2px solid #024c80;padding-bottom:6px;">
            Equipos Comprometidos
          </h3>
          <table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:20px;">
            <thead>
              <tr style="background:#f0f6fb;color:#024c80;text-align:left;">
                <th style="padding:8px 12px;border-bottom:2px solid #cbd5e1;">Artículo</th>
                <th style="padding:8px 12px;border-bottom:2px solid #cbd5e1;text-align:center;">Cant.</th>
                <th style="padding:8px 12px;border-bottom:2px solid #cbd5e1;">S/N o Detalle</th>
              </tr>
            </thead>
            <tbody>{equipment_rows_html}</tbody>
          </table>

          {f'<div style="background:#fffbeb;border-left:4px solid #f59e0b;padding:12px 16px;margin:16px 0;font-size:13px;"><strong>Observaciones:</strong> {reservation.notes}</div>' if reservation.notes else ''}

          <!-- Instrucción del acta -->
          <div style="background:#f0f6fb;border:1px solid #bfdbfe;border-radius:8px;padding:14px 16px;margin:20px 0;font-size:13px;color:#1e3a5f;">
            <strong>📎 Adjunto:</strong> Este correo incluye el <strong>Acta de Préstamo en PDF</strong> lista para ser impresa y firmada por ambas partes (DP&P y colaborador) antes y después del período de uso.
          </div>

          <!-- Botón Calendar -->
          <div style="margin-top:20px;text-align:center;">
            <a href="{calendar_link or '#'}" style="display:inline-block;padding:11px 22px;background:#024c80;
               color:#ffffff;text-decoration:none;border-radius:6px;font-weight:700;font-size:14px;">
              Ver Cita en Google Calendar →
            </a>
          </div>
        </div>

        <div style="background:#f8fafc;padding:14px 28px;text-align:center;font-size:11px;color:#94a3b8;border-top:1px solid #e2e8f0;">
          Grupo Tecfluid S.A. | Soporte TI: {support_emails_str}
        </div>
      </div>

      <!-- Acta renderizada debajo para clientes sin soporte de adjuntos -->
      <div style="max-width:640px;margin:28px auto 0;">
        <p style="font-size:12px;color:#94a3b8;text-align:center;margin-bottom:16px;">
          — Acta de Préstamo (versión web, referencia) —
        </p>
        {acta_html}
      </div>
    </body>
    </html>
    """

    plain_content = (
        f"Acta de Préstamo – Meta Quest\n"
        f"===============================\n\n"
        f"Solicitante: {reservation.kam_name} ({reservation.applicant_email})\n"
        f"Gerencia Comercial: {reservation.commercial_management}\n"
        f"Cliente: {reservation.client_name}\n"
        f"Fecha Solicitud: {reservation.request_date.strftime('%d/%m/%Y')}\n"
        f"Días de Préstamo: {reservation.duration_days}\n"
        f"Fecha de Devolución: {reservation.delivery_date.strftime('%d/%m/%Y')}\n\n"
        f"Equipos:\n{equipment_text}\n\n"
        + (f"Observaciones: {reservation.notes}\n\n" if reservation.notes else "")
        + f"Enlace Google Calendar: {calendar_link}\n"
        + f"Acta adjunta en PDF para firma física.\n"
        + f"Copias enviadas a: {support_emails_str}\n"
    )

    # ─────────────────────────────────────────────────────────────
    #  Construcción del mensaje MIME con adjunto PDF
    # ─────────────────────────────────────────────────────────────
    # Usamos "mixed" para poder incluir partes de texto/html + adjunto binario
    mime_message = MIMEMultipart("mixed")
    mime_message["Subject"] = subject
    mime_message["From"] = settings.GMAIL_SENDER_EMAIL
    mime_message["To"] = str(reservation.applicant_email)
    mime_message["Cc"] = ", ".join(settings.it_support_recipients)

    # Parte de texto + HTML (multipart/alternative anidado)
    alternative_part = MIMEMultipart("alternative")
    alternative_part.attach(MIMEText(plain_content, "plain", "utf-8"))
    alternative_part.attach(MIMEText(notification_html, "html", "utf-8"))
    mime_message.attach(alternative_part)

    # Adjuntar PDF si se generó correctamente
    if acta_pdf_bytes:
        pdf_filename = (
            f"Acta_Prestamo_MetaQuest_{reservation.client_name.replace(' ', '_')}_"
            f"{reservation.request_date.strftime('%Y%m%d')}.pdf"
        )
        pdf_part = MIMEApplication(acta_pdf_bytes, _subtype="pdf")
        pdf_part.add_header("Content-Disposition", "attachment", filename=pdf_filename)
        mime_message.attach(pdf_part)
        logger.info("PDF del Acta generado y adjunto al correo: %s", pdf_filename)

    raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode("utf-8")

    if not creds:
        logger.info(
            "[MODO SIMULACIÓN] Correo con Acta PDF hacia '%s' y '%s': %s",
            reservation.applicant_email, support_emails_str, subject
        )
        return {"sent": True, "is_mock": True, "message_id": "mock-msg-acta-001"}

    try:
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        sent_msg = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": raw_message})
            .execute()
        )
        logger.info("Correo con Acta PDF enviado. Message ID: %s", sent_msg.get("id"))
        return {"sent": True, "is_mock": False, "message_id": sent_msg.get("id")}
    except Exception as exc:
        logger.error("Error al enviar correo vía Gmail API: %s", exc)
        raise RuntimeError(f"Error en Gmail API: {exc}") from exc


def send_admin_otp_email(recipient_email: str, otp_code: str) -> Dict[str, Any]:
    """
    Envía un código de acceso único (OTP) de 6 dígitos al correo Gmail del administrador.
    """
    creds = get_google_credentials()
    subject = f"[Tecfluid VR Hub] Código de acceso Administrador: {otp_code}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
                 line-height:1.6;color:#1e293b;background-color:#0b1329;padding:24px;">
      <div style="max-width:520px;margin:0 auto;background:#0f172a;border:1px solid #1e293b;
                  border-radius:12px;overflow:hidden;box-shadow:0 10px 25px rgba(0,0,0,0.5);">
        <div style="background:#090d16;padding:20px 24px;border-bottom:2px solid #00d2ff;">
          <p style="color:#00d2ff;font-size:11px;margin:0 0 4px;text-transform:uppercase;letter-spacing:1px;font-weight:700;">
            Grupo Tecfluid — Seguridad de Acceso
          </p>
          <h2 style="color:#ffffff;margin:0;font-size:18px;font-weight:700;">
            Autenticación de Administrador
          </h2>
        </div>
        <div style="padding:28px 24px;color:#e2e8f0;text-align:center;">
          <p style="font-size:14px;color:#94a3b8;margin-top:0;">
            Has solicitado iniciar sesión en el <strong>Panel de Administración Meta Quest</strong>. Utiliza el siguiente código de seguridad temporal:
          </p>
          <div style="margin:24px 0;padding:16px;background:#090d16;border:1px dashed #38bdf8;border-radius:8px;">
            <span style="font-size:32px;font-weight:800;letter-spacing:8px;color:#38bdf8;font-family:monospace;">
              {otp_code}
            </span>
          </div>
          <p style="font-size:12px;color:#64748b;">
            Este código expirará en 10 minutos. Si tú no realizaste esta solicitud, por favor ignora este mensaje.
          </p>
        </div>
        <div style="background:#090d16;padding:12px 24px;text-align:center;font-size:11px;color:#64748b;border-top:1px solid #1e293b;">
          Grupo Tecfluid S.A. | Sistema de Préstamo VR Hub
        </div>
      </div>
    </body>
    </html>
    """

    plain_content = f"Tu código de acceso al Panel de Administración Meta Quest es: {otp_code}\nExpira en 10 minutos."

    mime_message = MIMEMultipart("alternative")
    mime_message["Subject"] = subject
    mime_message["From"] = settings.GMAIL_SENDER_EMAIL
    mime_message["To"] = recipient_email
    mime_message.attach(MIMEText(plain_content, "plain", "utf-8"))
    mime_message.attach(MIMEText(html_content, "html", "utf-8"))

    raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode("utf-8")

    if not creds:
        logger.info("[MODO SIMULACIÓN] Código OTP '%s' enviado a Gmail '%s'", otp_code, recipient_email)
        return {"sent": True, "is_mock": True, "code": otp_code}

    try:
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        sent_msg = service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        logger.info("Código OTP enviado a Gmail exitosamente. ID: %s", sent_msg.get("id"))
        return {"sent": True, "is_mock": False, "message_id": sent_msg.get("id")}
    except Exception as exc:
        logger.error("Error al enviar OTP vía Gmail API: %s", exc)
        raise RuntimeError(f"Error en Gmail API: {exc}") from exc


def send_user_otp_email(recipient_email: str, otp_code: str) -> Dict[str, Any]:
    """
    Envía un código de acceso único (OTP) de 6 dígitos a cualquier colaborador
    con correo corporativo @grupotecfluid.com que solicita acceso al portal de reservas.
    """
    creds = get_google_credentials()
    subject = f"[Tecfluid VR Hub] Tu código de acceso: {otp_code}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
                 line-height:1.6;color:#1e293b;background-color:#0b1329;padding:24px;">
      <div style="max-width:520px;margin:0 auto;background:#0f172a;border:1px solid #1e293b;
                  border-radius:12px;overflow:hidden;box-shadow:0 10px 25px rgba(0,0,0,0.5);">
        <div style="background:#090d16;padding:20px 24px;border-bottom:2px solid #0284c7;">
          <p style="color:#38bdf8;font-size:11px;margin:0 0 4px;text-transform:uppercase;letter-spacing:1px;font-weight:700;">
            Grupo Tecfluid — Portal de Reservas VR
          </p>
          <h2 style="color:#ffffff;margin:0;font-size:18px;font-weight:700;">
            Verificación de Correo Corporativo
          </h2>
        </div>
        <div style="padding:28px 24px;color:#e2e8f0;text-align:center;">
          <p style="font-size:14px;color:#94a3b8;margin-top:0;">
            Has solicitado acceder al sistema de <strong>Reserva de Visores Meta Quest</strong>. Ingresa el siguiente código de verificación en tu navegador:
          </p>
          <div style="margin:24px 0;padding:16px;background:#090d16;border:1px dashed #38bdf8;border-radius:8px;">
            <span style="font-size:32px;font-weight:800;letter-spacing:8px;color:#38bdf8;font-family:monospace;">
              {otp_code}
            </span>
          </div>
          <p style="font-size:12px;color:#64748b;">
            Este código de seguridad expirará en 10 minutos y es válido únicamente para tu cuenta corporativa.
          </p>
        </div>
        <div style="background:#090d16;padding:12px 24px;text-align:center;font-size:11px;color:#64748b;border-top:1px solid #1e293b;">
          Grupo Tecfluid S.A. | Soporte TI: {settings.IT_SUPPORT_EMAIL}
        </div>
      </div>
    </body>
    </html>
    """

    plain_content = (
        f"Tu código de acceso a Tecfluid VR Hub es: {otp_code}\n"
        f"Expira en 10 minutos.\n"
        f"Soporte: {settings.IT_SUPPORT_EMAIL}"
    )

    mime_message = MIMEMultipart("alternative")
    mime_message["Subject"] = subject
    mime_message["From"] = settings.GMAIL_SENDER_EMAIL
    mime_message["To"] = recipient_email
    mime_message.attach(MIMEText(plain_content, "plain", "utf-8"))
    mime_message.attach(MIMEText(html_content, "html", "utf-8"))

    raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode("utf-8")

    if not creds:
        logger.info("[MODO SIMULACIÓN] Código OTP usuario '%s' enviado a '%s'", otp_code, recipient_email)
        return {"sent": True, "is_mock": True, "code": otp_code}

    try:
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        sent_msg = service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        logger.info("Código OTP enviado a usuario exitosamente. ID: %s", sent_msg.get("id"))
        return {"sent": True, "is_mock": False, "message_id": sent_msg.get("id")}
    except Exception as exc:
        logger.error("Error al enviar OTP vía Gmail API: %s", exc)
        raise RuntimeError(f"Error en Gmail API: {exc}") from exc

