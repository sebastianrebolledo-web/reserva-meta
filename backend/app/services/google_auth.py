import logging
import os
from typing import Optional, List
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app.core.config import settings

logger = logging.getLogger(__name__)

# Scopes con principio de privilegios mínimos (solo eventos y solo envío de emails)
SCOPES: List[str] = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.send",
]


def get_google_credentials() -> Optional[Credentials]:
    """
    Obtiene y retorna credenciales válidas de Google según la configuración:
    1. Service Account (con soporte opcional para delegación de dominio)
    2. OAuth 2.0 (mediante refresh token)
    Retorna None si las credenciales no están configuradas (modo simulación/desarrollo).
    """
    try:
        # Modo 1: Service Account
        if settings.GOOGLE_AUTH_MODE == "service_account":
            sa_path = settings.GOOGLE_SERVICE_ACCOUNT_FILE
            if sa_path and os.path.isfile(sa_path):
                logger.info("Cargando credenciales de Google vía Service Account: %s", sa_path)
                creds = service_account.Credentials.from_service_account_file(
                    sa_path, scopes=SCOPES
                )
                if settings.GOOGLE_DELEGATED_USER:
                    creds = creds.with_subject(settings.GOOGLE_DELEGATED_USER)
                return creds
            else:
                logger.warning(
                    "Archivo de Service Account no encontrado en '%s'. "
                    "El servicio operará en modo simulado para pruebas locales.",
                    sa_path
                )
                return None

        # Modo 2: OAuth 2.0 con Refresh Token
        elif settings.GOOGLE_AUTH_MODE == "oauth2":
            if (
                settings.GOOGLE_CLIENT_ID
                and settings.GOOGLE_CLIENT_SECRET
                and settings.GOOGLE_REFRESH_TOKEN
            ):
                logger.info("Cargando credenciales de Google vía OAuth 2.0 Refresh Token")
                creds = Credentials(
                    None,
                    refresh_token=settings.GOOGLE_REFRESH_TOKEN,
                    client_id=settings.GOOGLE_CLIENT_ID,
                    client_secret=settings.GOOGLE_CLIENT_SECRET,
                    token_uri="https://oauth2.googleapis.com/token",
                    scopes=SCOPES,
                )
                if not creds.valid:
                    creds.refresh(Request())
                return creds
            else:
                logger.warning(
                    "Credenciales OAuth2 incompletas en variables de entorno. "
                    "El servicio operará en modo simulado para pruebas locales."
                )
                return None

        else:
            logger.warning("GOOGLE_AUTH_MODE '%s' no reconocido.", settings.GOOGLE_AUTH_MODE)
            return None

    except Exception as exc:
        logger.error("Error al inicializar credenciales de Google: %s", exc)
        return None
