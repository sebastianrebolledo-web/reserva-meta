"""
Operaciones CRUD sobre la base de datos SQLite.
Mantiene la lógica de negocio separada de la capa HTTP.
"""
import json
import logging
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from app.db.database import get_connection

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  INVENTARIO
# ─────────────────────────────────────────────────────────────────────────────

def get_all_inventory() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM inventario ORDER BY id").fetchall()
        return [dict(r) for r in rows]


def update_inventory_status(item_id: int, estado: str) -> bool:
    with get_connection() as conn:
        result = conn.execute(
            "UPDATE inventario SET estado = ? WHERE id = ?", (estado, item_id)
        )
        return result.rowcount > 0


# ─────────────────────────────────────────────────────────────────────────────
#  SOLICITUDES
# ─────────────────────────────────────────────────────────────────────────────

def _generate_folio() -> str:
    """Genera un folio único con formato MQ-YYYYMMDD-NNNN."""
    today = date.today().strftime("%Y%m%d")
    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM solicitudes WHERE folio LIKE ?",
            (f"MQ-{today}-%",)
        ).fetchone()[0]
    return f"MQ-{today}-{count + 1:04d}"


def create_solicitud(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Persiste una nueva solicitud de reserva.
    `data` debe contener los campos del esquema ReservationCreate
    más event_id y event_link obtenidos del servicio de Calendar.
    """
    folio = _generate_folio()
    equipment_json = json.dumps(data["equipment_details"], ensure_ascii=False)

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO solicitudes
                (folio, applicant_email, kam_name, commercial_management,
                 client_name, request_date, duration_days, delivery_date,
                 equipment_details, notes, event_id, event_link, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'En préstamo')
            """,
            (
                folio,
                data["applicant_email"],
                data["kam_name"],
                data["commercial_management"],
                data["client_name"],
                str(data["request_date"]),
                int(data["duration_days"]),
                str(data["delivery_date"]),
                equipment_json,
                data.get("notes") or "",
                data.get("event_id") or "",
                data.get("event_link") or "",
            ),
        )
        new_id = cursor.lastrowid

    return get_solicitud_by_id(new_id)  # type: ignore[return-value]


def get_all_solicitudes() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM solicitudes ORDER BY created_at DESC"
        ).fetchall()
        return [_parse_solicitud(dict(r)) for r in rows]


def get_solicitud_by_id(solicitud_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM solicitudes WHERE id = ?", (solicitud_id,)
        ).fetchone()
        return _parse_solicitud(dict(row)) if row else None


def get_solicitud_by_folio(folio: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM solicitudes WHERE folio = ?", (folio,)
        ).fetchone()
        return _parse_solicitud(dict(row)) if row else None


def update_solicitud_estado(solicitud_id: int, nuevo_estado: str) -> Optional[Dict[str, Any]]:
    """
    Cambia el estado de una solicitud.
    Cuando se marca como 'Entregado', no modifica inventario individual
    (los equipos del inventario se actualizan vía reglas de negocio en la capa de servicio).
    """
    valid_states = ("En préstamo", "Entregado", "Vencido")
    if nuevo_estado not in valid_states:
        raise ValueError(f"Estado inválido. Opciones: {valid_states}")

    with get_connection() as conn:
        result = conn.execute(
            "UPDATE solicitudes SET estado = ? WHERE id = ?",
            (nuevo_estado, solicitud_id)
        )
        if result.rowcount == 0:
            return None

    return get_solicitud_by_id(solicitud_id)


def get_kpi_summary() -> Dict[str, Any]:
    """KPIs para el panel de administración."""
    with get_connection() as conn:
        # Total de kits en inventario (equipos únicos, no accesorios individuales)
        total_equipos = conn.execute("SELECT COUNT(*) FROM inventario").fetchone()[0]

        # Solicitudes activas = kits actualmente en préstamo
        solicitudes_activas = conn.execute(
            "SELECT COUNT(*) FROM solicitudes WHERE estado = 'En préstamo'"
        ).fetchone()[0]

        # Disponibles = inventario total - kits actualmente en préstamo
        disponibles = max(0, total_equipos - solicitudes_activas)

        total_solicitudes = conn.execute("SELECT COUNT(*) FROM solicitudes").fetchone()[0]
        solicitudes_entregadas = conn.execute(
            "SELECT COUNT(*) FROM solicitudes WHERE estado = 'Entregado'"
        ).fetchone()[0]

    return {
        "total_equipos": total_equipos,
        "en_prestamo": solicitudes_activas,
        "disponibles": disponibles,
        "en_mantenimiento": 0,
        "total_solicitudes": total_solicitudes,
        "solicitudes_activas": solicitudes_activas,
        "solicitudes_entregadas": solicitudes_entregadas,
    }


def _parse_solicitud(row: Dict[str, Any]) -> Dict[str, Any]:
    """Deserializa el JSON de equipment_details y calcula estado automático."""
    try:
        row["equipment_details"] = json.loads(row.get("equipment_details") or "[]")
    except (json.JSONDecodeError, TypeError):
        row["equipment_details"] = []

    # Regla de negocio: marcar como Vencido si la fecha de devolución ya pasó
    try:
        delivery = date.fromisoformat(row["delivery_date"])
        if row["estado"] == "En préstamo" and delivery < date.today():
            row["estado"] = "Vencido"
    except (ValueError, TypeError, KeyError):
        pass

    return row
