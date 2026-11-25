from fastapi import APIRouter
from app.api.v1.endpoints import reservations, admin, auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación Corporativa"])
api_router.include_router(reservations.router, prefix="/reservations", tags=["Reservas"])
api_router.include_router(admin.router, prefix="/admin", tags=["Administración"])

9876