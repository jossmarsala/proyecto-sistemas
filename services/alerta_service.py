"""
alerta_service.py
Reads and manages system alerts (stock_minimo, limite_credito).
"""

from __future__ import annotations

from typing import List, Optional

from db.connection import get_connection
from models.alerta import AlertaResponse


def listar_alertas(
    tipo: Optional[str] = None,
    id_sucursal: Optional[int] = None,
    solo_activas: bool = True,
) -> List[AlertaResponse]:
    """Returns system alerts, optionally filtered by type or sucursal."""
    conn = get_connection()
    try:
        where = []
        params: list = []

        if solo_activas:
            where.append("activa = 1")
        if tipo:
            where.append("tipo = ?")
            params.append(tipo)
        if id_sucursal:
            where.append("id_sucursal = ?")
            params.append(id_sucursal)

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        rows = conn.execute(
            f"SELECT * FROM alertas {where_sql} ORDER BY fecha_hora DESC",
            params
        ).fetchall()

        return [
            AlertaResponse(
                id_alerta=r["id_alerta"],
                tipo=r["tipo"],
                id_referencia=r["id_referencia"],
                id_sucursal=r["id_sucursal"],
                mensaje=r["mensaje"],
                activa=r["activa"],
                fecha_hora=r["fecha_hora"],
            )
            for r in rows
        ]
    finally:
        conn.close()


def resolver_alerta(id_alerta: int) -> dict:
    """Marks an alert as resolved (activa = 0)."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM alertas WHERE id_alerta = ?", (id_alerta,)
        ).fetchone()
        if not row:
            raise ValueError(f"Alerta id={id_alerta} no encontrada.")

        conn.execute(
            "UPDATE alertas SET activa = 0 WHERE id_alerta = ?", (id_alerta,)
        )
        conn.commit()
        return {"id_alerta": id_alerta, "resuelta": True}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
