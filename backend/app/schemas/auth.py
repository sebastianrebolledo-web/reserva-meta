import re
from pydantic import BaseModel, Field, field_validator
from app.core.config import settings

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class RequestUserCodeRequest(BaseModel):
    email: str = Field(..., description="Correo corporativo del colaborador (@grupotecfluid.com)")

    @field_validator("email")
    @classmethod
    def validate_corporate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Formato de correo electrónico inválido.")
        domain = clean.split("@")[-1]
        expected = settings.CORPORATE_DOMAIN.strip().lower()
        if domain != expected:
            raise ValueError(
                f"Acceso restringido: Solo se permiten correos del dominio corporativo @{expected}"
            )
        return clean


class VerifyUserCodeRequest(BaseModel):
    email: str = Field(..., description="Correo corporativo del colaborador")
    code: str = Field(..., min_length=6, max_length=6, description="Código de 6 dígitos recibido por correo")

    @field_validator("email")
    @classmethod
    def clean_email(cls, v: str) -> str:
        return v.strip().lower()


class UserAuthResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    email: str
    role: str = "user"
    expires_in_hours: int
