import re
from pydantic import BaseModel, Field, field_validator
from typing import Optional

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class AdminLoginRequest(BaseModel):
    email: str = Field(..., description="Correo del administrador")
    password: str = Field(..., min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Formato de correo inválido.")
        return clean


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in_hours: int


class UpdateEstadoRequest(BaseModel):
    estado: str = Field(..., pattern=r"^(En préstamo|Entregado|Vencido)$")


class RequestCodeRequest(BaseModel):
    email: str = Field(..., description="Correo Gmail del administrador")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Formato de correo inválido.")
        return clean


class VerifyCodeRequest(BaseModel):
    email: str = Field(..., description="Correo Gmail del administrador")
    code: str = Field(..., min_length=6, max_length=6, description="Código de 6 dígitos")

