from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Sistema de Reserva Meta Quest"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # URL publica del frontend (para CORS en produccion)
    FRONTEND_URL: Optional[str] = None

    # Restriccion corporativa estricta
    CORPORATE_DOMAIN: str = "grupotecfluid.com"
    IT_SUPPORT_EMAIL: str = "soporteti@grupotecfluid.com"

    # Google Auth Settings
    GOOGLE_AUTH_MODE: str = "oauth2"  # "service_account" or "oauth2"
    GOOGLE_SERVICE_ACCOUNT_FILE: Optional[str] = "service-account.json"
    GOOGLE_DELEGATED_USER: Optional[str] = None

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REFRESH_TOKEN: Optional[str] = None

    GOOGLE_CALENDAR_ID: str = "primary"
    GMAIL_SENDER_EMAIL: str = "soporteti@grupotecfluid.com"

    # Administracion y seguridad
    SECRET_KEY: str = "change-me-in-production"
    JWT_EXPIRE_HOURS: int = 8
    ADMIN_EMAIL: str = "soporteti@grupotecfluid.com"
    ADMIN_PASSWORD: str = "changeme"

    # Base de datos SQLite (stdlib sqlite3)
    # En desarrollo: metaquest.db (relativo)
    # En produccion (Cloud Run): /app/data/metaquest.db (volumen persistente)
    DATABASE_URL: str = "metaquest.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        origins = [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
        if self.FRONTEND_URL and self.FRONTEND_URL.rstrip("/") not in origins:
            origins.append(self.FRONTEND_URL.rstrip("/"))
        return origins

    @property
    def it_support_recipients(self) -> List[str]:
        emails = [e.strip() for e in self.IT_SUPPORT_EMAIL.replace(";", ",").split(",") if e.strip()]
        for fallback in ["soporteti@grupotecfluid.com"]:
            if fallback not in emails:
                emails.append(fallback)
        return emails


settings = Settings()
