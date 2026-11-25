# Backend - Sistema de Reserva Meta Quest / Oculus

Backend modular desarrollado en **Python** con **FastAPI**, con tipado estricto, esquemas Pydantic y sincronización directa con **Google Calendar** y **Gmail**.

---

## 1. Requisitos
- Python 3.9+
- Entorno virtual en `backend/.venv`

---

## 2. Puesta en marcha

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Documentación interactiva disponible en:
- Swagger UI: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

---

## 3. Endpoints Principales

- `POST /api/v1/reservations`: Procesa una solicitud de reserva, valida el correo corporativo `@grupotecfluid.com`, calcula la fecha de entrega y crea el evento en Google Calendar y notifica por Gmail al solicitante y a `soporteti@grupotecfluid.com`.
- `GET /api/v1/reservations/health`: Verifica el estado de salud y la configuración corporativa.

---

## 4. Configuración con Google Cloud

Copia el archivo `.env.example` a `.env`:
```bash
cp .env.example .env
```

Puedes operar en dos modos:
1. **Modo Simulado (Desarrollo)**: Sin archivo de credenciales, el sistema simula las respuestas de Calendar y Gmail con logs explicativos.
2. **Modo Producción**:
   - Con **Service Account**: Colocar `service-account.json` y configurar `GOOGLE_AUTH_MODE="service_account"`.
   - Con **OAuth 2.0**: Configurar `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` y `GOOGLE_REFRESH_TOKEN`.
