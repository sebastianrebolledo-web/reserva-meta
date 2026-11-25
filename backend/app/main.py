import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router


# Configuración de logging estándar
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("metaquest_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.database import init_db
    init_db()
    logger.info("Base de datos SQLite inicializada exitosamente.")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API de reservas de visores y accesorios Meta Quest / Oculus con sincronización a Google Calendar y Gmail.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configuración de CORS segura
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de rutas v1
app.include_router(api_router, prefix="/api/v1")



@app.get("/", tags=["General"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "documentation": "/docs",
        "healthcheck": "/api/v1/reservations/health"
    }
