import re
from datetime import date, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from app.core.config import settings

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class EquipmentItem(BaseModel):
    name: str = Field(..., description="Nombre del equipo o accesorio (ej. Meta Quest 3, Controles Touch Plus)")
    quantity: int = Field(default=1, ge=1, description="Cantidad requerida")
    serial_or_notes: Optional[str] = Field(default=None, description="Número de serie o detalle adicional")


class ReservationBase(BaseModel):
    applicant_email: str = Field(..., description="Correo del solicitante (@grupotecfluid.com)")
    kam_name: str = Field(..., min_length=2, max_length=120, description="KAM Responsable")
    commercial_management: str = Field(..., min_length=2, max_length=120, description="Gerencia Comercial")
    client_name: str = Field(..., min_length=2, max_length=150, description="Nombre del cliente")
    request_date: date = Field(..., description="Fecha de inicio o solicitud del equipo")
    duration_days: int = Field(..., ge=1, le=90, description="Tiempo de petición en días")
    equipment_details: List[EquipmentItem] = Field(..., min_length=1, description="Detalles de los equipos y accesorios solicitados")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Observaciones o notas adicionales")

    @field_validator("applicant_email")
    @classmethod
    def validate_corporate_domain(cls, v: str) -> str:
        clean_email = v.strip().lower()
        if not EMAIL_REGEX.match(clean_email):
            raise ValueError("El formato del correo electrónico no es válido.")
        
        domain = clean_email.split("@")[-1]
        expected_domain = settings.CORPORATE_DOMAIN.strip().lower()
        if domain != expected_domain:
            raise ValueError(
                f"El correo debe pertenecer exclusivamente al dominio corporativo @{expected_domain}"
            )
        return clean_email


class ReservationCreate(ReservationBase):
    delivery_date: Optional[date] = Field(default=None, description="Fecha de entrega calculada")

    @model_validator(mode="after")
    def compute_delivery_date(self) -> "ReservationCreate":
        expected_date = self.request_date + timedelta(days=self.duration_days)
        if self.delivery_date is None:
            self.delivery_date = expected_date
        elif self.delivery_date != expected_date:
            # Asegura consistencia reactiva
            self.delivery_date = expected_date
        return self


class ReservationResponse(BaseModel):
    success: bool
    message: str
    event_id: Optional[str] = None
    event_link: Optional[str] = None
    email_notification_sent: bool = False
    applicant_email: str
    kam_name: str
    client_name: str
    request_date: date
    duration_days: int
    delivery_date: date
    equipment_summary: str
