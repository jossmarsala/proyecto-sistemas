"""
cliente_service.py
Business logic for client management and cuenta corriente ledger.
"""

from __future__ import annotations

import sqlite3
from typing import List, Optional

from db.connection import get_connection
from models.cliente import ClienteCreate, ClienteResponse, MovimientoCCResponse


def _row_to_cliente(row: sqlite3.Row) -> ClienteResponse:
    return ClienteResponse(
        id_cliente=row["id_cliente"],
        nombre=row["nombre"],
        apellido=row["apellido"],
        cuit_dni=row["cuit_dni"],
        razon_social=row["razon_social"],
        telefono=row["telefono"],
        notas=row["notas"],
        saldo_cuenta_corriente=row["saldo_cuenta_corriente"],
        limite_credito=row["limite_credito"],
        creado_en=row["creado_en"],
    )


def crear_cliente(data: ClienteCreate) -> ClienteResponse:
    """Creates a new client record."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO clientes (nombre, apellido, cuit_dni, razon_social, telefono, notas, limite_credito)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (data.nombre, data.apellido, data.cuit_dni, data.razon_social,
             data.telefono, data.notas, data.limite_credito)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM clientes WHERE id_cliente = ?", (cur.lastrowid,)).fetchone()
        return _row_to_cliente(row)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def listar_clientes(
    nombre: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
) -> List[ClienteResponse]:
    """Returns paginated client list, optionally filtered by name (LIKE)."""
    conn = get_connection()
    try:
        params: list = []
        where = ""
        if nombre:
            where = "WHERE (nombre LIKE ? OR apellido LIKE ? OR razon_social LIKE ?)"
            pattern = f"%{nombre}%"
            params = [pattern, pattern, pattern]

        offset = (page - 1) * limit
        params += [limit, offset]

        rows = conn.execute(
            f"SELECT * FROM clientes {where} ORDER BY nombre LIMIT ? OFFSET ?",
            params
        ).fetchall()

        return [_row_to_cliente(r) for r in rows]
    finally:
        conn.close()


def get_cliente(id_cliente: int) -> ClienteResponse:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM clientes WHERE id_cliente = ?", (id_cliente,)
        ).fetchone()
        if not row:
            raise ValueError(f"Cliente id={id_cliente} no encontrado.")
        return _row_to_cliente(row)
    finally:
        conn.close()


def get_cuenta_corriente(
    id_cliente: int,
    page: int = 1,
    limit: int = 50,
) -> List[MovimientoCCResponse]:
    """Returns the cuenta corriente ledger for a client (newest first)."""
    conn = get_connection()
    try:
        # Verify client exists
        exists = conn.execute(
            "SELECT 1 FROM clientes WHERE id_cliente = ?", (id_cliente,)
        ).fetchone()
        if not exists:
            raise ValueError(f"Cliente id={id_cliente} no encontrado.")

        offset = (page - 1) * limit
        rows = conn.execute(
            """SELECT * FROM cuenta_corriente
               WHERE id_cliente = ?
               ORDER BY fecha_hora DESC
               LIMIT ? OFFSET ?""",
            (id_cliente, limit, offset)
        ).fetchall()

        return [
            MovimientoCCResponse(
                id_movimiento=r["id_movimiento"],
                id_cliente=r["id_cliente"],
                id_venta=r["id_venta"],
                tipo=r["tipo"],
                monto=r["monto"],
                saldo_resultante=r["saldo_resultante"],
                notas=r["notas"],
                fecha_hora=r["fecha_hora"],
            )
            for r in rows
        ]
    finally:
        conn.close()


def registrar_pago_cc(id_cliente: int, monto: float, notas: Optional[str] = None) -> ClienteResponse:
    """
    Records a payment (pago) to a client's cuenta corriente,
    reducing their saldo_cuenta_corriente.
    """
    if monto <= 0:
        raise ValueError("El monto del pago debe ser mayor a 0.")

    conn = get_connection()
    try:
        conn.execute("BEGIN")
        cliente = conn.execute(
            "SELECT * FROM clientes WHERE id_cliente = ?", (id_cliente,)
        ).fetchone()
        if not cliente:
            raise ValueError(f"Cliente id={id_cliente} no encontrado.")

        nuevo_saldo = round(cliente["saldo_cuenta_corriente"] - monto, 2)

        conn.execute(
            """INSERT INTO cuenta_corriente (id_cliente, tipo, monto, saldo_resultante, notas)
               VALUES (?, 'pago', ?, ?, ?)""",
            (id_cliente, monto, nuevo_saldo, notas)
        )
        conn.execute(
            "UPDATE clientes SET saldo_cuenta_corriente = ? WHERE id_cliente = ?",
            (nuevo_saldo, id_cliente)
        )
        conn.commit()

        row = conn.execute("SELECT * FROM clientes WHERE id_cliente = ?", (id_cliente,)).fetchone()
        return _row_to_cliente(row)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
