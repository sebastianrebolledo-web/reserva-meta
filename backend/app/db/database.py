"""
Capa de persistencia SQLite usando el módulo estándar sqlite3.
Sin ORM: consultas directas para máxima ligereza y cero dependencias extra.
"""
import sqlite3
import json
import logging
from contextlib import contextmanager
from pathlib import Path
from app.core.config import settings

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
raw_db_path = Path(settings.DATABASE_URL)
DB_PATH = raw_db_path if raw_db_path.is_absolute() else (BACKEND_DIR / raw_db_path)
logger = logging.getLogger(__name__)



@contextmanager
def get_connection():
    """Context manager que abre, confirma/revierte y cierra la conexión."""
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row  # Acceso por nombre de columna
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Crea las tablas si no existen e inserta el inventario base de equipos."""
    with get_connection() as conn:
        conn.executescript("""
            -- ──────────────────────────────────────────
            -- Inventario de equipos
            -- ──────────────────────────────────────────
            CREATE TABLE IF NOT EXISTS inventario (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                modelo         TEXT    NOT NULL,
                numero_serie   TEXT    DEFAULT '',
                estado         TEXT    NOT NULL DEFAULT 'Disponible'
                                   CHECK(estado IN ('Disponible', 'En préstamo', 'En mantenimiento'))
            );

            -- ──────────────────────────────────────────
            -- Solicitudes de reserva
            -- ──────────────────────────────────────────
            CREATE TABLE IF NOT EXISTS solicitudes (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                folio               TEXT    UNIQUE NOT NULL,
                applicant_email     TEXT    NOT NULL,
                kam_name            TEXT    NOT NULL,
                commercial_management TEXT  NOT NULL,
                client_name         TEXT    NOT NULL,
                request_date        TEXT    NOT NULL,
                duration_days       INTEGER NOT NULL,
                delivery_date       TEXT    NOT NULL,
                equipment_details   TEXT    NOT NULL,  -- JSON string
                notes               TEXT    DEFAULT '',
                event_id            TEXT    DEFAULT '',
                event_link          TEXT    DEFAULT '',
                estado              TEXT    NOT NULL DEFAULT 'En préstamo'
                                        CHECK(estado IN ('En préstamo', 'Entregado', 'Vencido')),
                created_at          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
            );
        """)

        # Insertar inventario base si la tabla está vacía
        count = conn.execute("SELECT COUNT(*) FROM inventario").fetchone()[0]
        if count == 0:
            base_inventory = [
                ("Kit Meta Quest 3 – Completo #1", "MQ3-KIT-001"),
                ("Kit Meta Quest 3 – Completo #2", "MQ3-KIT-002"),
                ("Kit Meta Quest 3 – Completo #3", "MQ3-KIT-003"),
                ("Kit Meta Quest 3 – Completo #4", "MQ3-KIT-004"),
            ]
            conn.executemany(
                "INSERT INTO inventario (modelo, numero_serie) VALUES (?, ?)",
                base_inventory
            )
            logger.info("Inventario base inicializado con %d kits Meta Quest.", len(base_inventory))

    logger.info("Base de datos SQLite inicializada en: %s", DB_PATH.resolve())
